from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from lumen.core.models import ItemCategory, SearchResult


@dataclass
class NavigationLevel:
    title: str
    items: List[SearchResult] = field(default_factory=list)
    search_query: str = ""
    provider_filter: Optional[str] = None
    placeholder_text: str = "Type to search..."
    icon_name: str = "system-search"


class NavigationManager:
    ROOT_CATEGORIES: List[SearchResult] = [
        SearchResult(
            id="nav:apps",
            title="Apps",
            subtitle="Search and launch applications",
            category=ItemCategory.APPLICATION.value,
            icon_name="applications-other",
            subcommands=[]
        ),
        SearchResult(
            id="nav:packages",
            title="Packages",
            subtitle="Install, remove, and manage software",
            category=ItemCategory.PACKAGE.value,
            icon_name="package-x-generic",
            subcommands=[]
        ),
        SearchResult(
            id="nav:updates",
            title="Updates",
            subtitle="Lumen and system software updates",
            category=ItemCategory.PACKAGE.value,
            icon_name="software-update-available",
            subcommands=[]
        ),
        SearchResult(
            id="nav:commands",
            title="Commands",
            subtitle="Custom commands and scripts",
            category=ItemCategory.COMMAND.value,
            icon_name="utilities-terminal",
            subcommands=[]
        ),
        SearchResult(
            id="nav:files",
            title="Files",
            subtitle="Locations and recent files",
            category=ItemCategory.LOCATION.value,
            icon_name="folder",
            subcommands=[]
        ),
        SearchResult(
            id="nav:system",
            title="System",
            subtitle="Lock, suspend, restart, settings",
            category=ItemCategory.SYSTEM.value,
            icon_name="preferences-system",
            subcommands=[]
        )
    ]

    def __init__(self) -> None:
        self._stack: List[NavigationLevel] = []

    def push(self, level: NavigationLevel) -> None:
        self._stack.append(level)

    def pop(self) -> Optional[NavigationLevel]:
        if not self._stack:
            return None
        return self._stack.pop()

    def reset(self) -> None:
        self._stack.clear()

    def depth(self) -> int:
        return len(self._stack)

    def current_level(self) -> Optional[NavigationLevel]:
        if not self._stack:
            return None
        return self._stack[-1]

    def is_at_root(self) -> bool:
        return len(self._stack) == 0

    def get_root_categories(self) -> List[SearchResult]:
        return self.ROOT_CATEGORIES

    def breadcrumb_path(self) -> str:
        if not self._stack:
            return ""
        path_parts = ["Lumen"] + [level.title for level in self._stack]
        return " › ".join(path_parts)
