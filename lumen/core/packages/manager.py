"""
Aggregated package manager controller and multi-backend orchestrator.
"""

from __future__ import annotations

import threading
from typing import Callable, Dict, List, Optional

from lumen.core.logging import debug, error, info
from lumen.core.packages.apt import AptBackend
from lumen.core.packages.base import BasePackageBackend, PackageInfo, PackageOperationResult
from lumen.core.packages.flatpak import FlatpakBackend
from lumen.core.packages.pacman import PacmanBackend
from lumen.core.packages.snap import SnapBackend


class PackageManager:
    """Orchestrates multi-backend software management, search, and operations."""

    _instance: Optional["PackageManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.backends: Dict[str, BasePackageBackend] = {
            "apt": AptBackend(),
            "flatpak": FlatpakBackend(),
            "snap": SnapBackend(),
            "pacman": PacmanBackend(),
        }
        self._op_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "PackageManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def get_available_backends(self) -> List[BasePackageBackend]:
        """Returns list of installed/active package managers on the current system."""
        return [b for b in self.backends.values() if b.is_available()]

    def get_backend(self, backend_id: str) -> Optional[BasePackageBackend]:
        return self.backends.get(backend_id.lower())

    def search_all(self, query: str, limit: int = 15) -> List[PackageInfo]:
        """Searches across all available backends and ranks results."""
        if not query.strip():
            return []

        all_pkgs: List[PackageInfo] = []
        for backend in self.get_available_backends():
            try:
                res = backend.search(query, limit=limit)
                all_pkgs.extend(res)
            except Exception as e:
                error("PackageManager", f"Search error in {backend.name}: {e}")

        # Sort: installed first, then exact matches, then GUI apps
        q_lower = query.lower()
        def _rank_key(p: PackageInfo) -> tuple[int, int, int]:
            exact = 0 if p.name.lower() == q_lower else 1
            installed = 0 if p.installed else 1
            gui = 0 if p.is_gui_app else 1
            return (installed, exact, gui)

        all_pkgs.sort(key=_rank_key)
        return all_pkgs[:limit]

    def search_all_async(
        self,
        query: str,
        callback: Callable[[List[PackageInfo]], None],
        limit: int = 15,
    ) -> threading.Thread:
        """Runs search_all in a background thread and invokes callback with results."""
        def _worker():
            results = self.search_all(query, limit=limit)
            try:
                callback(results)
            except Exception as e:
                error("PackageManager", f"Async search callback error: {e}")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def check_all_updates_async(
        self,
        callback: Callable[[Dict[str, List[PackageInfo]]], None],
    ) -> threading.Thread:
        """Runs check_all_updates in a background thread and invokes callback with results."""
        def _worker():
            updates = self.check_all_updates()
            try:
                callback(updates)
            except Exception as e:
                error("PackageManager", f"Async update check callback error: {e}")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def check_all_updates(self) -> Dict[str, List[PackageInfo]]:
        """Queries all active backends for pending updates."""
        updates: Dict[str, List[PackageInfo]] = {}
        for backend in self.get_available_backends():
            try:
                up = backend.check_updates()
                if up:
                    updates[backend.name] = up
            except Exception as e:
                debug("PackageManager", f"Update check in {backend.name}: {e}")
        return updates

    def get_total_update_count(self) -> int:
        """Returns total count of available updates across all backends."""
        updates = self.check_all_updates()
        return sum(len(pkgs) for pkgs in updates.values())

    def install(
        self,
        package_name: str,
        backend_id: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> PackageOperationResult:
        """Installs a package using the specified or best available backend."""
        if not self._op_lock.acquire(blocking=False):
            return PackageOperationResult(
                success=False,
                message="Another package operation is currently in progress",
                error_details="Concurrent lock active",
            )
        try:
            target_backend: Optional[BasePackageBackend] = None
            if backend_id:
                target_backend = self.get_backend(backend_id)
            else:
                # Pick first available backend that has the package
                for b in self.get_available_backends():
                    matches = b.search(package_name, limit=5)
                    if any(m.name.lower() == package_name.lower() for m in matches):
                        target_backend = b
                        break
                if not target_backend:
                    available = self.get_available_backends()
                    if available:
                        target_backend = available[0]

            if not target_backend:
                return PackageOperationResult(
                    success=False,
                    message=f"No package manager available to install '{package_name}'",
                )

            return target_backend.install(package_name, on_progress=on_progress)
        finally:
            self._op_lock.release()

    def remove(
        self,
        package_name: str,
        backend_id: Optional[str] = None,
        purge: bool = False,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> PackageOperationResult:
        """Removes a package with confirmation support."""
        if not self._op_lock.acquire(blocking=False):
            return PackageOperationResult(
                success=False,
                message="Another package operation is currently in progress",
                error_details="Concurrent lock active",
            )
        try:
            target_backend: Optional[BasePackageBackend] = None
            if backend_id:
                target_backend = self.get_backend(backend_id)
            else:
                for b in self.get_available_backends():
                    installed = b.list_installed(package_name, limit=5)
                    if any(p.name.lower() == package_name.lower() for p in installed):
                        target_backend = b
                        break
                if not target_backend:
                    available = self.get_available_backends()
                    if available:
                        target_backend = available[0]

            if not target_backend:
                return PackageOperationResult(
                    success=False,
                    message=f"No package manager available to remove '{package_name}'",
                )

            return target_backend.remove(package_name, purge=purge, on_progress=on_progress)
        finally:
            self._op_lock.release()

    def update_all(self, on_progress: Optional[Callable[[str], None]] = None) -> Dict[str, PackageOperationResult]:
        """Runs update across all available backends."""
        if not self._op_lock.acquire(blocking=False):
            return {
                "system": PackageOperationResult(
                    success=False,
                    message="Another package operation is currently in progress",
                    error_details="Concurrent lock active",
                )
            }
        try:
            results: Dict[str, PackageOperationResult] = {}
            for backend in self.get_available_backends():
                try:
                    if on_progress:
                        on_progress(f"Updating {backend.name}...")
                    res = backend.update(on_progress=on_progress)
                    results[backend.name] = res
                except Exception as e:
                    results[backend.name] = PackageOperationResult(
                        success=False,
                        message=f"{backend.name} update failed: {e}",
                        error_details=str(e),
                    )
            return results
        finally:
            self._op_lock.release()
