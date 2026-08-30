"""
APT / Dpkg package management backend for Debian/Ubuntu-based distributions.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from lumen.core.logging import debug, error, info
from lumen.core.packages.base import BasePackageBackend, PackageInfo, PackageOperationResult


class AptBackend(BasePackageBackend):
    """Integrates with Debian/Ubuntu APT and Dpkg package tools."""

    @property
    def name(self) -> str:
        return "APT"

    @property
    def backend_id(self) -> str:
        return "apt"

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
            "supports_details": True,
        }

    def is_available(self) -> bool:
        return bool(shutil.which("apt-cache") or shutil.which("dpkg"))

    def is_locked(self) -> bool:
        """Checks whether dpkg/apt locks are held by another process."""
        lock_files = [
            Path("/var/lib/dpkg/lock-frontend"),
            Path("/var/lib/dpkg/lock"),
            Path("/var/lib/apt/lists/lock"),
        ]
        for lock_file in lock_files:
            if lock_file.exists():
                try:
                    # Check if file is locked via fcntl test or lsof/fuser
                    res = subprocess.run(["fuser", str(lock_file)], capture_output=True, text=True)
                    if res.returncode == 0 and res.stdout.strip():
                        return True
                except Exception:
                    pass
        return False

    def search(self, query: str, limit: int = 15) -> List[PackageInfo]:
        if not self.is_available() or not query.strip():
            return []

        results: List[PackageInfo] = []
        try:
            # First search names
            cmd = ["apt-cache", "search", "--names-only", query]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                for line in res.stdout.splitlines()[:limit]:
                    parts = line.split(" - ", 1)
                    if len(parts) == 2:
                        pkg_name = parts[0].strip()
                        summary = parts[1].strip()
                        results.append(
                            PackageInfo(
                                name=pkg_name,
                                summary=summary,
                                source_backend="apt",
                                icon_name="package-x-generic",
                            )
                        )
        except Exception as e:
            error("APT", f"Search error for '{query}': {e}")

        # Check installed status for results
        if results:
            self._enrich_installed_status(results)

        return results

    def _enrich_installed_status(self, packages: List[PackageInfo]) -> None:
        """Checks dpkg-query status to flag which packages are already installed."""
        if not packages or not shutil.which("dpkg-query"):
            return
        try:
            pkg_names = [p.name for p in packages]
            cmd = ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${Status}\n"] + pkg_names
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.stdout:
                status_map = {}
                for line in res.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        status_map[parts[0]] = (parts[1], "installed" in parts[2])
                for p in packages:
                    if p.name in status_map:
                        ver, inst = status_map[p.name]
                        p.installed = inst
                        if inst:
                            p.version = ver
        except Exception:
            pass

    def list_installed(self, query: str = "", limit: int = 30) -> List[PackageInfo]:
        if not shutil.which("dpkg-query"):
            return []
        results: List[PackageInfo] = []
        try:
            cmd = ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${Status}\t${binary:Summary}\n"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            if res.returncode == 0:
                q_lower = query.lower()
                for line in res.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 4 and "installed" in parts[2]:
                        name = parts[0]
                        summary = parts[3]
                        if not q_lower or (q_lower in name.lower() or q_lower in summary.lower()):
                            results.append(
                                PackageInfo(
                                    name=name,
                                    version=parts[1],
                                    summary=summary,
                                    source_backend="apt",
                                    installed=True,
                                )
                            )
                            if len(results) >= limit:
                                break
        except Exception as e:
            error("APT", f"List installed failed: {e}")
        return results

    def check_updates(self) -> List[PackageInfo]:
        if not shutil.which("apt"):
            return []
        updates: List[PackageInfo] = []
        try:
            res = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "/" in line and not line.startswith("Listing..."):
                        parts = line.split()
                        if len(parts) >= 2:
                            pkg_name = parts[0].split("/")[0]
                            new_ver = parts[1]
                            updates.append(
                                PackageInfo(
                                    name=pkg_name,
                                    source_backend="apt",
                                    update_available=True,
                                    new_version=new_ver,
                                    summary="Upgrade available",
                                )
                            )
        except Exception as e:
            debug("APT", f"Check updates: {e}")
        return updates

    def install(self, package_name: str, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not re.match(r"^[a-zA-Z0-9_\-\.\+]+$", package_name):
            return PackageOperationResult(success=False, message="Invalid package name characters", error_details="Security validation failed")

        if self.is_locked():
            return PackageOperationResult(success=False, message="APT is currently busy with another operation", error_details="Lock file active")

        if on_progress:
            on_progress(f"Installing {package_name} via APT...")

        # Run with pkexec for elevation
        cmd = ["pkexec", "apt-get", "install", "-y", package_name]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode == 0:
                info("APT", f"Successfully installed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully installed {package_name} via APT",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                err_msg = res.stderr or res.stdout
                error("APT", f"Install failed: {err_msg}")
                return PackageOperationResult(
                    success=False,
                    message=f"Could not install {package_name}",
                    raw_output=res.stdout,
                    error_details=err_msg,
                )
        except subprocess.TimeoutExpired:
            return PackageOperationResult(success=False, message="Installation timed out", error_details="Process exceeded 5 minutes")
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Installation error: {e}", error_details=str(e))

    def remove(self, package_name: str, purge: bool = False, on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if not re.match(r"^[a-zA-Z0-9_\-\.\+]+$", package_name):
            return PackageOperationResult(success=False, message="Invalid package name characters", error_details="Security validation failed")

        if self.is_locked():
            return PackageOperationResult(success=False, message="APT is currently busy with another operation", error_details="Lock file active")

        if on_progress:
            on_progress(f"Removing {package_name} via APT...")

        action_flag = "--purge" if purge else "remove"
        cmd = ["pkexec", "apt-get", "remove", "-y"]
        if purge:
            cmd.append("--purge")
        cmd.append(package_name)

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode == 0:
                info("APT", f"Successfully removed {package_name}")
                return PackageOperationResult(
                    success=True,
                    message=f"Successfully removed {package_name} via APT",
                    raw_output=res.stdout,
                    affected_packages=[package_name],
                )
            else:
                err_msg = res.stderr or res.stdout
                return PackageOperationResult(
                    success=False,
                    message=f"Could not remove {package_name}",
                    raw_output=res.stdout,
                    error_details=err_msg,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Removal error: {e}", error_details=str(e))

    def update(self, package_name: str = "", on_progress: Optional[Callable[[str], None]] = None) -> PackageOperationResult:
        if self.is_locked():
            return PackageOperationResult(success=False, message="APT is currently busy with another operation", error_details="Lock file active")

        if package_name:
            if on_progress:
                on_progress(f"Upgrading {package_name} via APT...")
            cmd = ["pkexec", "apt-get", "install", "--only-upgrade", "-y", package_name]
        else:
            if on_progress:
                on_progress("Updating APT package indexes and upgrading packages...")
            cmd = ["pkexec", "sh", "-c", "apt-get update && apt-get upgrade -y"]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode == 0:
                msg = f"Upgraded {package_name} via APT" if package_name else "All APT packages updated successfully"
                return PackageOperationResult(success=True, message=msg, raw_output=res.stdout)
            else:
                return PackageOperationResult(
                    success=False,
                    message="APT update failed",
                    raw_output=res.stdout,
                    error_details=res.stderr or res.stdout,
                )
        except Exception as e:
            return PackageOperationResult(success=False, message=f"Update error: {e}", error_details=str(e))
