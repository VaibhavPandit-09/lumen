"""
Commands search provider for user and agent defined commands and nested menus.
"""

from __future__ import annotations

from typing import List, Optional

from lumen.core.fuzzy import score_item
from lumen.core.models import CommandItem, ItemCategory, SearchResult
from lumen.core.runner import launch_shell_command
from lumen.providers.base import BaseProvider


def command_item_to_search_result(
    cmd: CommandItem, parent_path: str = ""
) -> SearchResult:
    """Converts a CommandItem definition into an actionable SearchResult."""
    item_id = f"cmd:{parent_path}/{cmd.name}" if parent_path else f"cmd:{cmd.name}"
    display_category = cmd.category or ItemCategory.COMMAND.value

    sub_results: List[SearchResult] = []
    if cmd.subcommands:
        new_parent = f"{parent_path}/{cmd.name}" if parent_path else cmd.name
        for sub in cmd.subcommands:
            sub_results.append(command_item_to_search_result(sub, parent_path=new_parent))

    badge = "Group" if cmd.subcommands else ("Terminal" if cmd.terminal else "Cmd")

    action = None
    if cmd.command:
        action = lambda c=cmd.command, t=cmd.terminal, d=cmd.cwd, e=cmd.env: launch_shell_command(
            c, terminal=t, cwd=d, env=e
        )

    return SearchResult(
        id=item_id,
        title=cmd.name,
        subtitle=cmd.description or (f"Nested menu ({len(cmd.subcommands)} items)" if cmd.subcommands else cmd.command),
        category=display_category,
        icon_name=cmd.icon or "utilities-terminal",
        action=action,
        subcommands=sub_results,
        badge=badge,
        keywords=cmd.keywords,
        shortcut_hint=cmd.shortcut,
        context={"command": cmd.command, "terminal": cmd.terminal, "cwd": cmd.cwd},
    )


class CommandProvider(BaseProvider):
    """Searches user-defined and agent-defined commands and nested groups."""

    def __init__(self, commands: Optional[List[CommandItem]] = None, enabled: bool = True):
        super().__init__("commands", enabled=enabled)
        self.commands: List[CommandItem] = commands or []
        self._cached_results: List[SearchResult] = []

    def set_commands(self, commands: List[CommandItem]) -> None:
        self.commands = commands
        self.refresh()

    def initialize(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Builds top-level search results from configured command items."""
        self._cached_results = [
            command_item_to_search_result(c) for c in self.commands
        ]

    def _search_recursive(
        self, items: List[SearchResult], query: str, results: List[SearchResult]
    ) -> None:
        """Recursively matches query against item tree for direct global searching."""
        q = query.strip()
        for item in items:
            matched, score = score_item(
                query=q,
                title=item.title,
                subtitle=item.subtitle,
                keywords=item.keywords,
                category=item.category,
            )
            if matched and score > 0:
                scored = SearchResult(
                    id=item.id,
                    title=item.title,
                    subtitle=item.subtitle,
                    category=item.category,
                    icon_name=item.icon_name,
                    score=score + 20.0,  # Bonus boost for custom user commands
                    action=item.action,
                    subcommands=item.subcommands,
                    badge=item.badge,
                    keywords=item.keywords,
                    shortcut_hint=item.shortcut_hint,
                    context=item.context,
                )
                results.append(scored)

            # Search inside subcommands if query is provided
            if q and item.subcommands:
                self._search_recursive(item.subcommands, query, results)

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        results: List[SearchResult] = []
        self._search_recursive(self._cached_results, query, results)
        return results
