"""
Search provider for user and agent-created custom actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from lumen.core.actions.discovery import ActionScanner
from lumen.core.actions.executor import ActionExecutor
from lumen.core.actions.manifest import ActionDefinition
from lumen.core.fuzzy import score_item
from lumen.core.logging import debug
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.base import BaseProvider


class CustomActionsProvider(BaseProvider):
    """Integrates discovered custom actions into the search pipeline."""

    def __init__(self, actions_dir: Optional[Union[str, Path]] = None, enabled: bool = True):
        super().__init__("actions", enabled=enabled)
        self.scanner = ActionScanner(actions_dir)
        self._actions: List[ActionDefinition] = []

    def initialize(self) -> None:
        """Loads and indexes actions from disk."""
        if self.enabled:
            self._actions = self.scanner.scan()
            self.scanner.setup_watcher(on_change=self.refresh)

    def refresh(self) -> None:
        """Reloads actions from the scanner."""
        self._actions = self.scanner.scan()

    def get_actions(self) -> List[ActionDefinition]:
        """Returns the list of loaded actions."""
        return list(self._actions)

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        q = query.strip()
        results: List[SearchResult] = []

        for act in self._actions:
            if not act.is_valid:
                continue

            if not q:
                # Top level list of all actions
                score = 50.0
                matched = True
            else:
                matched, score = score_item(
                    query=q,
                    title=act.name,
                    subtitle=act.description,
                    keywords=act.keywords,
                    category=ItemCategory.CUSTOM_ACTION.value,
                )

            if matched:
                item = SearchResult(
                    id=f"action:{act.id}",
                    title=act.name,
                    subtitle=act.description or "Custom Action",
                    category=ItemCategory.CUSTOM_ACTION.value,
                    icon_name=act.icon,
                    score=score,
                    action=lambda a=act: ActionExecutor.execute(a),
                    badge="Action",
                    keywords=act.keywords,
                    origin_provider="actions",
                    requires_confirmation=act.confirm,
                    confirm_prompt=act.confirm_message or f"Confirm: {act.name}?",
                    action_id=act.id,
                )
                results.append(item)

        return results
