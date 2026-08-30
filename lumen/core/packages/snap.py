"""
Snap package management backend for Canonical Snappy packages.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Callable, List, Optional

from lumen.core.logging import debug, error, info
from lumen.core.packages.base import BasePackageBackend, PackageInfo, PackageOperationResult


class SnapBackend(BasePackageBackend):
    """Integrates with Ubuntu Snap packaging."""

    @property
    def name(self) -> str:
        return "Snap"

    @property
    def backend_id(self) -> str:
        return "snap"

    def is_available(self) -> bool:
        return bool(shutil.which("snap"))

    def is_locked(self) -> bool:
        return False

    def search(self, query: str, limit: int = 15) -> List[PackageInfo]:
        if not self.is_available() or not query.strip():
            return []

        results: List[PackageInfo] = []
        try:
            cmd = ["snap", "find", query]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                lines = res.stdout.splitlines()
                # Skip header line
                for line in lines[1:limit + 1]:
                    parts = line.split(maxsplit=4)
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        summary = parts[4] if len(parts) >= 5 else ""
                        results.append(
                            PackageInfo(
                                name=name,
                                version=version,
                                summary=summary,
                                source_backend="snap",
                                icon_name="package-x-generic",
                            )
                        )
        except Exception as e:
            error("Snap", f"Search error for '{query}': {e}")
        return results

    def list_installed(self, query: str = "", limit: int = 30) -> List[PackageInfo]:
        if not self.is_available():
            return []

        results: List[PackageInfo] = []
        try:
            cmd = ["snap", "list"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                lines = res.stdout.splitlines()
                q_lower = query.lower()
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        if not q_lower or q_lower in name.lower():
                            results.append(
                                PackageInfo(
                                    name=name,
                                    version=version,
                                    source_backend="snap",
                                    installed=True,
                                )
                            )
                            if len(results) >= limit:
                                break
        except Exception as e:
            error("Snap", f"List installed error: {e}")
        return results

    def check_updates(self) -> List[PackageInfo]:
        if not self.is_available():
            return []

        updates: List[PackageInfo] = []
        try:
            cmd = ["snap", "refresh", "--list"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                lines = res.stdout.splitlines()
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        updates.append(
                            PackageInfo(
                                name=parts[0],
                                source_backend="snap",
                                update_available=True,
                                new_version=parts[1],
                                summary="Snap update available",
                            )
                        )
        except Exception as e:
            debug("Snap", f"Check updates: {e}")
        return updates

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_search": True,
            "supports_installed": True,
            "supports_updates": True,
            "supports_install": True,
            "supports_remove": True,
            "supports_purge": False,
            "supports_update": True,
            "supports_details": False,
        }

    def install(self, package_name: str, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_valid_package_name(package_name):
            return PackageOperationResult(success=False, message="Invalid package name characters", error_details="Security validation failed")

        if not self.is_available():
            return PackageOperationResult(success=False, message="Snap is not installed on this system")

        if on_progress:
            on_progress(f"Installing {package_name} via Snap...")

        cmd = ["pkexec", "snap", "install", package_name]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode == 0:
                info("Snap", f"Successfully installed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully installed {package_name} via Snap",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                return PackageOperationResult(
                    success=False,
                    message=f"Could not install {package_name} via Snap",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Snap install error: {e}", error_details=str(e))

    def remove(self, package_name: str, purge: bool = False, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_valid_package_name(package_name):
            return PackageOperationResult(success=False, message="Invalid package name characters", error_details="Security validation failed")

        if not self.is_available():
            return PackageOperationResult(success=False, message="Snap is not installed on this system")

        if on_progress:
            on_progress(f"Removing {package_name} via Snap...")

        cmd = ["pkexec", "snap", "remove", package_name]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode == 0:
                info("Snap", f"Successfully removed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully removed {package_name} via Snap",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                return PackageOperationResult(
                    success=False,
                    message=f"Could not remove {package_name} via Snap",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Snap remove error: {e}", error_details=str(e))

    def update(self, package_name: str = "", on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_available():
            return PackageOperationResult(success=False, message="Snap is not installed on this system")

        if package_name:
            if on_progress:
                on_progress(f"Updating {package_name} via Snap...")
            cmd = ["pkexec", "snap", "refresh", package_name]
        else:
            if on_progress:
                on_progress("Updating all Snap packages...")
            cmd = ["pkexec", "snap", "refresh"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode == 0:
                return PackageOperationResult(success=True, message="Snap update completed", raw_output=res.stdout)
            else:
                return PackageOperationResult(
                    success=False,
                    message="Snap update failed",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Snap update error: {e}", error_details=str(e))
