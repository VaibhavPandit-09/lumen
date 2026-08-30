"""
Search provider integrating universal package management and software intents.
"""

from __future__ import annotations

from typing import List

from lumen.core.models import ActionPayload, ActionType, ItemCategory, SearchResult
from lumen.core.packages.base import PackageInfo
from lumen.core.packages.intent import CommandIntent, IntentParser, IntentType
from lumen.core.packages.manager import PackageManager
from lumen.providers.base import BaseProvider


class PackagesProvider(BaseProvider):
    """Provides software search, natural package commands, and update actions."""

    def __init__(self, enabled: bool = True):
        super().__init__(name="PackagesProvider", enabled=enabled)
        self.manager = PackageManager.get_instance()

    def initialize(self) -> None:
        self.manager = PackageManager.get_instance()

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query.strip():
            return []

        q = query.strip()
        intent = IntentParser.parse(q)
        results: List[SearchResult] = []

        # 1. Handle Update All / Updates Intent
        if intent.intent_type == IntentType.UPDATE_ALL:
            updates = self.manager.check_all_updates()
            total_count = sum(len(pkgs) for pkgs in updates.values())
            sub = f"{total_count} updates available across {', '.join(updates.keys())}" if total_count else "Check and apply updates for all package managers"

            def _do_update_all():
                return self.manager.update_all()

            results.append(
                SearchResult(
                    id="pkg:update_all",
                    title="Update All Software",
                    subtitle=sub,
                    category=ItemCategory.PACKAGE.value,
                    icon_name="system-software-update",
                    score=1.0,
                    badge="System Update",
                    payload=ActionPayload(
                        action_type=ActionType.SYSTEM_UPDATE_ALL,
                        handler=_do_update_all,
                        is_async=True,
                        success_message="All software updated successfully",
                        error_message="Software update encountered an issue",
                    ),
                )
            )
            return results

        # 2. Handle Explicit Install Intent (e.g. "install htop")
        elif intent.intent_type == IntentType.INSTALL and intent.target:
            target = intent.target
            matches = self.manager.search_all(target, limit=5)
            if not matches:
                # Provide direct install action
                def _do_install(name=target):
                    return self.manager.install(name)

                results.append(
                    SearchResult(
                        id=f"pkg:install:{target}",
                        title=f"Install '{target}'",
                        subtitle=f"Install software package via available package manager",
                        category=ItemCategory.PACKAGE.value,
                        icon_name="system-software-install",
                        score=0.95,
                        badge="Install",
                        payload=ActionPayload(
                            action_type=ActionType.PACKAGE_INSTALL,
                            target=target,
                            handler=_do_install,
                            is_async=True,
                            success_message=f"Installed {target} successfully",
                        ),
                    )
                )
            else:
                for pkg in matches:
                    results.append(self._pkg_to_search_result(pkg, score=0.95, force_install=True))
            return results

        # 3. Handle Explicit Remove Intent (e.g. "uninstall htop")
        elif intent.intent_type == IntentType.REMOVE and intent.target:
            target = intent.target

            def _do_remove(name=target):
                return self.manager.remove(name)

            results.append(
                SearchResult(
                    id=f"pkg:remove:{target}",
                    title=f"Uninstall '{target}'",
                    subtitle=f"Remove package from system",
                    category=ItemCategory.PACKAGE.value,
                    icon_name="edit-delete",
                    score=0.95,
                    badge="Uninstall",
                    requires_confirmation=True,
                    confirm_prompt=f"Are you sure you want to uninstall '{target}'?",
                    payload=ActionPayload(
                        action_type=ActionType.PACKAGE_REMOVE,
                        target=target,
                        handler=_do_remove,
                        is_async=True,
                        is_destructive=True,
                        confirm_prompt=f"Uninstall '{target}' from system?",
                        success_message=f"Uninstalled {target} successfully",
                    ),
                )
            )
            return results

        # 4. Handle General Software Search (query length >= 3)
        elif len(q) >= 3 and not q.startswith(("/", ">", "=", "$")):
            matches = self.manager.search_all(q, limit=6)
            for pkg in matches:
                results.append(self._pkg_to_search_result(pkg, score=0.65))

        return results

    def _pkg_to_search_result(self, pkg: PackageInfo, score: float = 0.7, force_install: bool = False) -> SearchResult:
        """Converts a PackageInfo dataclass into a SearchResult."""
        action_verb = "Install" if (not pkg.installed or force_install) else "Manage"
        badge = f"{pkg.source_backend.upper()}"
        icon = pkg.icon_name or "package-x-generic"

        if not pkg.installed or force_install:
            def _install_action(name=pkg.name, b_id=pkg.source_backend):
                return self.manager.install(name, backend_id=b_id)

            payload = ActionPayload(
                action_type=ActionType.PACKAGE_INSTALL,
                target=pkg.name,
                handler=_install_action,
                is_async=True,
                success_message=f"Installed {pkg.name} ({pkg.source_backend.upper()})",
            )
            subtitle = f"{action_verb} {pkg.source_backend.upper()} package • {pkg.summary}" if pkg.summary else f"{action_verb} {pkg.source_backend.upper()} package"
        else:
            def _remove_action(name=pkg.name, b_id=pkg.source_backend):
                return self.manager.remove(name, backend_id=b_id)

            payload = ActionPayload(
                action_type=ActionType.PACKAGE_REMOVE,
                target=pkg.name,
                handler=_remove_action,
                is_async=True,
                is_destructive=True,
                confirm_prompt=f"Uninstall {pkg.name} ({pkg.source_backend.upper()})?",
                success_message=f"Uninstalled {pkg.name}",
            )
            subtitle = f"Installed {pkg.source_backend.upper()} package • {pkg.summary}" if pkg.summary else f"Installed {pkg.source_backend.upper()} package"

        return SearchResult(
            id=f"pkg:{pkg.source_backend}:{pkg.name}",
            title=pkg.name,
            subtitle=subtitle,
            category=ItemCategory.PACKAGE.value,
            icon_name=icon,
            score=score,
            badge=badge,
            payload=payload,
            requires_confirmation=payload.is_destructive,
            confirm_prompt=payload.confirm_prompt,
        )
