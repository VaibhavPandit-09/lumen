"""
Pacman package management backend for Arch Linux and derivative distributions.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from lumen.core.logging import debug, error, info
from lumen.core.packages.base import BasePackageBackend, PackageInfo, PackageOperationResult


class PacmanBackend(BasePackageBackend):
    """Integrates with Arch Linux Pacman package manager."""

    @property
    def name(self) -> str:
        return "Pacman"

    @property
    def backend_id(self) -> str:
        return "pacman"

    def is_available(self) -> bool:
        return bool(shutil.which("pacman"))

    def is_locked(self) -> bool:
        return Path("/var/lib/pacman/db.lck").exists()

    def search(self, query: str, limit: int = 15) -> List[PackageInfo]:
        if not self.is_available() or not query.strip():
            return []

        results: List[PackageInfo] = []
        try:
            cmd = ["pacman", "-Ss", query]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                lines = res.stdout.splitlines()
                # Pacman outputs in pairs:
                # repo/pkgname version [installed]
                #     description
                i = 0
                while i < len(lines) and len(results) < limit:
                    line = lines[i]
                    if line.startswith(" ") or not line.strip():
                        i += 1
                        continue
                    parts = line.split()
                    if parts:
                        repo_pkg = parts[0]
                        pkg_name = repo_pkg.split("/")[-1] if "/" in repo_pkg else repo_pkg
                        ver = parts[1] if len(parts) > 1 else ""
                        is_installed = "[installed]" in line

                        desc = ""
                        if i + 1 < len(lines) and lines[i + 1].startswith("    "):
                            desc = lines[i + 1].strip()
                            i += 1

                        results.append(
                            PackageInfo(
                                name=pkg_name,
                                version=ver,
                                summary=desc,
                                source_backend="pacman",
                                installed=is_installed,
                                icon_name="package-x-generic",
                            )
                        )
                    i += 1
        except Exception as e:
            error("Pacman", f"Search error for '{query}': {e}")
        return results

    def list_installed(self, query: str = "", limit: int = 30) -> List[PackageInfo]:
        if not self.is_available():
            return []

        results: List[PackageInfo] = []
        try:
            cmd = ["pacman", "-Qs", query] if query else ["pacman", "-Q"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                lines = res.stdout.splitlines()
                for line in lines:
                    if not line.startswith(" "):
                        parts = line.split()
                        if parts:
                            pkg_name = parts[0].split("/")[-1] if "/" in parts[0] else parts[0]
                            ver = parts[1] if len(parts) > 1 else ""
                            results.append(
                                PackageInfo(
                                    name=pkg_name,
                                    version=ver,
                                    source_backend="pacman",
                                    installed=True,
                                )
                            )
                            if len(results) >= limit:
                                break
        except Exception as e:
            error("Pacman", f"List installed error: {e}")
        return results

    def check_updates(self) -> List[PackageInfo]:
        if not self.is_available():
            return []

        updates: List[PackageInfo] = []
        try:
            cmd = ["pacman", "-Qu"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 4:
                        pkg_name = parts[0]
                        curr_ver = parts[1]
                        new_ver = parts[3]
                        updates.append(
                            PackageInfo(
                                name=pkg_name,
                                version=curr_ver,
                                new_version=new_ver,
                                source_backend="pacman",
                                update_available=True,
                                summary=f"Update: {curr_ver} -> {new_ver}",
                            )
                        )
        except Exception as e:
            debug("Pacman", f"Check updates: {e}")
        return updates

    def install(self, package_name: str, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_available():
            return PackageOperationResult(success=False, message="Pacman is not available on this system")

        if self.is_locked():
            return PackageOperationResult(success=False, message="Pacman database is currently locked", error_details="/var/lib/pacman/db.lck active")

        if on_progress:
            on_progress(f"Installing {package_name} via Pacman...")

        cmd = ["pkexec", "pacman", "-S", "--noconfirm", package_name]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode == 0:
                info("Pacman", f"Successfully installed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully installed {package_name} via Pacman",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                return PackageOperationResult(
                    success=False,
                    message=f"Could not install {package_name} via Pacman",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Pacman install error: {e}", error_details=str(e))

    def remove(self, package_name: str, purge: bool = False, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_available():
            return PackageOperationResult(success=False, message="Pacman is not available on this system")

        if self.is_locked():
            return PackageOperationResult(success=False, message="Pacman database is currently locked", error_details="/var/lib/pacman/db.lck active")

        if on_progress:
            on_progress(f"Removing {package_name} via Pacman...")

        cmd = ["pkexec", "pacman", "-Rns" if purge else "-R", "--noconfirm", package_name]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode == 0:
                info("Pacman", f"Successfully removed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully removed {package_name} via Pacman",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                return PackageOperationResult(
                    success=False,
                    message=f"Could not remove {package_name} via Pacman",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Pacman remove error: {e}", error_details=str(e))

    def update(self, package_name: str = "", on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_available():
            return PackageOperationResult(success=False, message="Pacman is not available on this system")

        if self.is_locked():
            return PackageOperationResult(success=False, message="Pacman database is currently locked", error_details="/var/lib/pacman/db.lck active")

        if package_name:
            if on_progress:
                on_progress(f"Upgrading {package_name} via Pacman...")
            cmd = ["pkexec", "pacman", "-S", "--noconfirm", package_name]
        else:
            if on_progress:
                on_progress("Upgrading all Arch packages with pacman -Syu...")
            cmd = ["pkexec", "pacman", "-Syu", "--noconfirm"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            if res.returncode == 0:
                return PackageOperationResult(success=True, message="Pacman system upgrade complete", raw_output=res.stdout)
            else:
                return PackageOperationResult(
                    success=False,
                    message="Pacman upgrade failed",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Pacman upgrade error: {e}", error_details=str(e))
