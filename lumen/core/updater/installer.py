"""
Installer module for self-updating functionality.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from lumen.core.logging import debug, error, info
from lumen.core.updater.checker import UpdateInfo


class InstallMethod(Enum):
    """Supported installation methods."""
    USER_LOCAL = "user_local"
    DEBIAN = "debian"
    ARCH = "arch"
    PIP = "pip"
    DEVELOPMENT = "development"
    UNKNOWN = "unknown"


@dataclass
class UpdateResult:
    """Outcome of a self-update attempt."""
    success: bool
    message: str
    new_version: str = ""
    rollback_performed: bool = False


class SelfUpdater:
    """Handles applying updates for the self-contained installation."""

    @classmethod
    def detect_install_method(cls) -> InstallMethod:
        """Heuristics to detect how the application was installed."""
        if Path(__file__).parents[3].joinpath(".git").exists():
            return InstallMethod.DEVELOPMENT

        local_bin_wrapper = Path.home() / ".local" / "bin" / "lumen"
        if local_bin_wrapper.exists():
            return InstallMethod.USER_LOCAL

        try:
            if subprocess.run(["dpkg", "-s", "lumen"], capture_output=True).returncode == 0:
                return InstallMethod.DEBIAN
        except FileNotFoundError:
            pass

        try:
            if subprocess.run(["pacman", "-Q", "lumen-launcher"], capture_output=True).returncode == 0:
                return InstallMethod.ARCH
        except FileNotFoundError:
            pass

        try:
            if subprocess.run(["pip", "show", "lumen-launcher"], capture_output=True).returncode == 0:
                return InstallMethod.PIP
        except FileNotFoundError:
            pass

        return InstallMethod.UNKNOWN

    @classmethod
    def can_self_update(cls, method: InstallMethod) -> bool:
        """Determines if the current installation method supports self-updating."""
        return method == InstallMethod.USER_LOCAL

    def update(self, update_info: UpdateInfo, on_progress: Optional[Callable[[str], None]] = None) -> UpdateResult:
        """
        Perform self-update. Supported only for USER_LOCAL installs.
        """
        method = self.detect_install_method()
        if not self.can_self_update(method):
            return UpdateResult(
                success=False,
                message=f"Cannot self-update. Installation method is {method.value}. Please use your package manager."
            )

        def report_progress(msg: str) -> None:
            if on_progress:
                on_progress(msg)
            info("SelfUpdater", msg)

        try:
            updates_dir = Path.home() / ".cache" / "lumen" / "updates"
            updates_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.TemporaryDirectory(dir=updates_dir) as staging_dir:
                staging_path = Path(staging_dir)
                tarball_path = staging_path / "update.tar.gz"

                report_progress("Downloading source tarball...")
                urllib.request.urlretrieve(update_info.download_url, tarball_path)

                if update_info.checksum_url:
                    report_progress("Downloading checksums...")
                    checksums_path = staging_path / "SHA256SUMS"
                    urllib.request.urlretrieve(update_info.checksum_url, checksums_path)
                    
                    report_progress("Verifying checksum...")
                    expected_hash = ""
                    with open(checksums_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if "update.tar.gz" in line or "lumen" in line:
                                expected_hash = line.split()[0]
                                break
                    
                    if expected_hash:
                        hasher = hashlib.sha256()
                        with open(tarball_path, "rb") as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                hasher.update(chunk)
                        
                        if hasher.hexdigest() != expected_hash:
                            return UpdateResult(success=False, message="Checksum verification failed.")

                report_progress("Extracting files...")
                with tarfile.open(tarball_path, "r:gz") as tar:
                    def is_within_directory(directory: str, target: str) -> bool:
                        abs_directory = os.path.abspath(directory)
                        abs_target = os.path.abspath(target)
                        prefix = os.path.commonprefix([abs_directory, abs_target])
                        return prefix == abs_directory

                    def safe_extract(tar_ref: tarfile.TarFile, path: str = ".") -> None:
                        for member in tar_ref.getmembers():
                            member_path = os.path.join(path, member.name)
                            if not is_within_directory(path, member_path):
                                raise Exception("Attempted Path Traversal in Tar File")
                        tar_ref.extractall(path)
                        
                    safe_extract(tar, str(staging_path))

                # Find extracted package structure
                extracted_lumen_dir = None
                for root, dirs, files in os.walk(staging_path):
                    if "lumen" in dirs and os.path.exists(os.path.join(root, "lumen", "__init__.py")):
                        extracted_lumen_dir = Path(root)
                        break

                if not extracted_lumen_dir:
                    return UpdateResult(success=False, message="Invalid update package structure.")

                report_progress("Finding installation path...")
                wrapper_path = Path.home() / ".local" / "bin" / "lumen"
                target_install_dir = None
                
                if wrapper_path.exists():
                    with open(wrapper_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        for line in content.splitlines():
                            if "cd " in line:
                                potential_dir = line.split("cd ")[1].strip().strip('"\'')
                                if Path(potential_dir).exists():
                                    target_install_dir = Path(potential_dir)
                                    break
                            elif "python" in line and "lumen" in line:
                                parts = line.split()
                                for part in parts:
                                    if "lumen" in part and Path(part).parent.exists():
                                        target_install_dir = Path(part).parent
                                        break
                                        
                fallback_dir = Path.home() / ".local" / "share" / "lumen"
                if target_install_dir is None and fallback_dir.exists():
                    target_install_dir = fallback_dir

                if not target_install_dir or not target_install_dir.exists():
                    return UpdateResult(success=False, message="Could not determine installation path.")

                backup_dir = target_install_dir.with_suffix(".backup")
                
                report_progress("Creating backup...")
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(str(target_install_dir), str(backup_dir))

                try:
                    report_progress("Installing new version...")
                    shutil.copytree(extracted_lumen_dir, target_install_dir)

                    report_progress("Verifying installation...")
                    verify_cmd = [
                        "python3", "-c", 
                        "import sys; import os; sys.path.insert(0, os.getcwd()); import lumen; print(lumen.__version__)"
                    ]
                    result = subprocess.run(verify_cmd, cwd=target_install_dir, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise RuntimeError(f"Verification failed: {result.stderr}")
                        
                    new_ver = result.stdout.strip()
                    
                    report_progress("Cleaning up...")
                    shutil.rmtree(backup_dir)
                    
                    return UpdateResult(success=True, message="Update successful", new_version=new_ver)

                except Exception as e:
                    report_progress(f"Installation failed, rolling back: {e}")
                    if target_install_dir.exists():
                        shutil.rmtree(target_install_dir)
                    shutil.move(str(backup_dir), str(target_install_dir))
                    return UpdateResult(success=False, message=str(e), rollback_performed=True)

        except Exception as e:
            error("SelfUpdater", f"Update process failed: {e}")
            return UpdateResult(success=False, message=str(e))
