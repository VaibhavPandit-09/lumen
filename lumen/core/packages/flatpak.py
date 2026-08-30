"""
Flatpak package management backend for desktop application sandboxes.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Callable, List, Optional

from lumen.core.logging import debug, error, info
from lumen.core.packages.base import BasePackageBackend, PackageInfo, PackageOperationResult


class FlatpakBackend(BasePackageBackend):
    """Integrates with Flatpak application framework."""

    @property
    def name(self) -> str:
        return "Flatpak"

    @property
    def backend_id(self) -> str:
        return "flatpak"

    def is_available(self) -> bool:
        return bool(shutil.which("flatpak"))

    def is_locked(self) -> bool:
        return False  # Flatpak supports per-app transactions

    def search(self, query: str, limit: int = 15) -> List[PackageInfo]:
        if not self.is_available() or not query.strip():
            return []

        results: List[PackageInfo] = []
        try:
            cmd = ["flatpak", "search", "--columns=application,name,description,version", query]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                for line in res.stdout.splitlines()[:limit]:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        app_id = parts[0].strip()
                        name = parts[1].strip()
                        desc = parts[2].strip() if len(parts) > 2 else ""
                        ver = parts[3].strip() if len(parts) > 3 else ""
                        results.append(
                            PackageInfo(
                                name=app_id,
                                summary=f"{name} — {desc}" if desc else name,
                                version=ver,
                                source_backend="flatpak",
                                is_gui_app=True,
                                icon_name=app_id,
                            )
                        )
        except Exception as e:
            error("Flatpak", f"Search error for '{query}': {e}")
        return results

    def list_installed(self, query: str = "", limit: int = 30) -> List[PackageInfo]:
        if not self.is_available():
            return []

        results: List[PackageInfo] = []
        try:
            cmd = ["flatpak", "list", "--columns=application,name,version"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                q_lower = query.lower()
                for line in res.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        app_id = parts[0].strip()
                        name = parts[1].strip()
                        ver = parts[2].strip() if len(parts) > 2 else ""
                        if not q_lower or (q_lower in app_id.lower() or q_lower in name.lower()):
                            results.append(
                                PackageInfo(
                                    name=app_id,
                                    summary=name,
                                    version=ver,
                                    source_backend="flatpak",
                                    installed=True,
                                    is_gui_app=True,
                                )
                            )
                            if len(results) >= limit:
                                break
        except Exception as e:
            error("Flatpak", f"List installed error: {e}")
        return results

    def check_updates(self) -> List[PackageInfo]:
        if not self.is_available():
            return []

        updates: List[PackageInfo] = []
        try:
            cmd = ["flatpak", "remote-ls", "--updates"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 1 and parts[0].strip():
                        updates.append(
                            PackageInfo(
                                name=parts[0].strip(),
                                source_backend="flatpak",
                                update_available=True,
                                summary="Flatpak update available",
                            )
                        )
        except Exception as e:
            debug("Flatpak", f"Check updates: {e}")
        return updates

    @property
    def capabilities(self) -> Dict[str, bool]:
        return {
            "supports_search": True,
            "supports_installed": True,
            "supports_updates": True,
            "supports_install": True,
            "supports_remove": True,
            "supports_purge": True,
            "supports_update": True,
            "supports_details": False,
        }

    def install(self, package_name: str, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_valid_package_name(package_name):
            return PackageOperationResult(success=False, message="Invalid package name characters", error_details="Security validation failed")

        if not self.is_available():
            return PackageOperationResult(success=False, message="Flatpak is not installed on this system")

        if on_progress:
            on_progress(f"Installing {package_name} via Flatpak...")

        cmd = ["flatpak", "install", "-y", package_name]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode == 0:
                info("Flatpak", f"Successfully installed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully installed {package_name} via Flatpak",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                return PackageOperationResult(
                    success=False,
                    message=f"Could not install {package_name} via Flatpak",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Flatpak install error: {e}", error_details=str(e))

    def remove(self, package_name: str, purge: bool = False, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_valid_package_name(package_name):
            return PackageOperationResult(success=False, message="Invalid package name characters", error_details="Security validation failed")

        if not self.is_available():
            return PackageOperationResult(success=False, message="Flatpak is not installed on this system")

        if on_progress:
            on_progress(f"Uninstalling {package_name} via Flatpak...")

        cmd = ["flatpak", "uninstall", "-y", package_name]
        if purge:
            cmd.append("--delete-data")

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode == 0:
                info("Flatpak", f"Successfully uninstalled {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully uninstalled {package_name} via Flatpak",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                return PackageOperationResult(
                    success=False,
                    message=f"Could not uninstall {package_name} via Flatpak",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Flatpak remove error: {e}", error_details=str(e))

    def update(self, package_name: str = "", on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not self.is_available():
            return PackageOperationResult(success=False, message="Flatpak is not installed on this system")

        if package_name:
            if on_progress:
                on_progress(f"Updating {package_name} via Flatpak...")
            cmd = ["flatpak", "update", "-y", package_name]
        else:
            if on_progress:
                on_progress("Updating all Flatpak applications...")
            cmd = ["flatpak", "update", "-y"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode == 0:
                return PackageOperationResult(success=True, message="Flatpak update completed", raw_output=res.stdout)
            else:
                return PackageOperationResult(
                    success=False,
                    message="Flatpak update failed",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Flatpak update error: {e}", error_details=str(e))
