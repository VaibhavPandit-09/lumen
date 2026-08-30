"""
Provider for Lumen self-updates and system software updates.
"""

from __future__ import annotations

from typing import List, Optional

from lumen import __version__
from lumen.core.actions.dispatcher import ActionType
from lumen.core.logging import debug, error, info
from lumen.core.models import ActionPayload, ItemCategory, SearchResult
from lumen.core.packages.base import PackageOperationResult
from lumen.core.packages.manager import PackageManager
from lumen.core.updater.checker import UpdateChecker, UpdateInfo
from lumen.core.updater.installer import InstallMethod, SelfUpdater, UpdateResult
from lumen.providers.base import BaseProvider


class UpdatesProvider(BaseProvider):
    """Provides Lumen self-update status and system package updates."""

    def __init__(self, enabled: bool = True):
        super().__init__(name="UpdatesProvider", enabled=enabled)
        self.manager: Optional[PackageManager] = None
        self.checker: Optional[UpdateChecker] = None
        self._cached_lumen_update: Optional[UpdateInfo] = None

    def initialize(self) -> None:
        """Initializes package manager and update checker."""
        try:
            self.manager = PackageManager.get_instance()
            self.checker = UpdateChecker()
            # Fast check from local cache
            self._cached_lumen_update = self.checker._load_cache()
        except Exception as e:
            error("UpdatesProvider", f"Initialization error: {e}")

    def refresh(self) -> None:
        """Refreshes update state."""
        self.initialize()

    def search(self, query: str) -> List[SearchResult]:
        """Returns pending Lumen and system package updates."""
        if not self.enabled:
            return []

        q = query.strip().lower()
        results: List[SearchResult] = []

        # 1. Lumen self-update item
        lumen_item = self._get_lumen_update_item()
        if lumen_item:
            if not q or "lumen" in q or "update" in q or "self" in q:
                results.append(lumen_item)

        # 2. System updates items
        system_items = self._get_system_update_items(q)
        results.extend(system_items)

        # Empty state when on updates surface
        if not results and (q in ("update", "updates", "upgrade", "")):
            results.append(
                SearchResult(
                    id="update:all_current",
                    title="All software is up to date",
                    subtitle=f"Lumen v{__version__} • No pending package updates detected",
                    category=ItemCategory.PACKAGE.value,
                    icon_name="emblem-ok",
                    badge="Up to date",
                    is_empty_state=True,
                )
            )

        return results

    def _get_lumen_update_item(self) -> Optional[SearchResult]:
        """Builds a search result for Lumen self-update if available."""
        info = self._cached_lumen_update
        if not info and self.checker:
            info = self.checker._load_cache()

        if not info or not info.update_available:
            return None

        # Check if dismissed
        if self.checker and self.checker.is_dismissed(info):
            return None

        def _do_self_update() -> UpdateResult:
            updater = SelfUpdater()
            return updater.update(info)

        desc = info.release_notes.replace("\n", " ").strip()
        if len(desc) > 80:
            desc = desc[:77] + "..."

        sub = f"v{info.current_version} → v{info.latest_version}"
        if desc:
            sub += f" • {desc}"

        return SearchResult(
            id="update:lumen_self",
            title=f"Update Lumen to v{info.latest_version}",
            subtitle=sub,
            category=ItemCategory.PACKAGE.value,
            icon_name="software-update-available",
            badge="Lumen Update",
            score=100.0,
            payload=ActionPayload(
                action_type=ActionType.LUMEN_INTERNAL,
                target="self_update",
                handler=_do_self_update,
                is_async=True,
                success_message=f"Lumen updated to v{info.latest_version}. Restarting...",
                error_message="Lumen update failed",
            ),
        )

    def _get_system_update_items(self, query: str) -> List[SearchResult]:
        """Builds search results for system package updates."""
        if not self.manager:
            return []

        results: List[SearchResult] = []
        try:
            updates = self.manager.check_all_updates()
            total_count = sum(len(pkgs) for pkgs in updates.values())

            if total_count > 0:
                # "Update All" meta-action
                def _do_update_all() -> PackageOperationResult:
                    res_dict = self.manager.update_all()
                    all_succ = all(r.success for r in res_dict.values())
                    summary = "; ".join(f"{k}: {v.message}" for k, v in res_dict.items())
                    return PackageOperationResult(
                        success=all_succ,
                        message=summary or "All software updated successfully",
                    )

                results.append(
                    SearchResult(
                        id="update:all_system",
                        title="Update All System Software",
                        subtitle=f"{total_count} pending updates across {len(updates)} package managers",
                        category=ItemCategory.PACKAGE.value,
                        icon_name="system-software-update",
                        badge="Update All",
                        score=95.0,
                        payload=ActionPayload(
                            action_type=ActionType.SYSTEM_UPDATE_ALL,
                            handler=_do_update_all,
                            is_async=True,
                            success_message="System update completed successfully",
                            error_message="System update encountered errors",
                        ),
                    )
                )

                # Per-backend items
                for backend_name, pkgs in updates.items():
                    if not pkgs:
                        continue
                    backend_id = pkgs[0].source_backend if pkgs else backend_name.lower()
                    pkg_sample = ", ".join(p.name for p in pkgs[:4])
                    if len(pkgs) > 4:
                        pkg_sample += f" and {len(pkgs) - 4} more"

                    def _make_backend_updater(b_id=backend_id, b_name=backend_name):
                        def _updater():
                            b = self.manager.get_backend(b_id)
                            if b:
                                return b.update()
                            return PackageOperationResult(success=False, message=f"Backend {b_name} unavailable")
                        return _updater

                    results.append(
                        SearchResult(
                            id=f"update:backend:{backend_name.lower()}",
                            title=f"Update {backend_name} Software",
                            subtitle=f"{len(pkgs)} updates: {pkg_sample}",
                            category=ItemCategory.PACKAGE.value,
                            icon_name="package-x-generic",
                            badge=backend_name,
                            score=90.0,
                            payload=ActionPayload(
                                action_type=ActionType.PACKAGE_UPDATE,
                                target=backend_id,
                                handler=_make_backend_updater(),
                                is_async=True,
                                success_message=f"{backend_name} update completed",
                                error_message=f"{backend_name} update failed",
                            ),
                        )
                    )
        except Exception as e:
            debug("UpdatesProvider", f"System updates check error: {e}")

        return results
