"""
Data structures and models for Lumen items, actions, and search results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ItemCategory(str, Enum):
    APPLICATION = "Applications"
    COMMAND = "Commands"
    SYSTEM = "System Actions"
    LOCATION = "Locations"
    CALCULATION = "Calculator"
    RECENT = "Recent Files"
    CLIPBOARD = "Clipboard"
    WEB = "Web Search"


@dataclass
class SearchResult:
    """Represents a single actionable search result in Lumen."""
    id: str
    title: str
    subtitle: str = ""
    category: str = ItemCategory.APPLICATION.value
    icon_name: str = "application-x-executable"
    score: float = 0.0
    action: Optional[Callable[[], Any]] = None
    subcommands: List["SearchResult"] = field(default_factory=list)
    badge: str = ""
    keywords: List[str] = field(default_factory=list)
    shortcut_hint: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def execute(self) -> Any:
        """Executes the action associated with this search result."""
        if self.action is not None and callable(self.action):
            return self.action()
        return None

    def has_subcommands(self) -> bool:
        """Whether this item can be drilled down into."""
        return bool(self.subcommands)


@dataclass
class CommandItem:
    """User-configured or agent-created command definition."""
    name: str
    command: str = ""
    description: str = ""
    icon: str = "utilities-terminal"
    category: str = "Commands"
    terminal: bool = False
    cwd: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    subcommands: List["CommandItem"] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    shortcut: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        d: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
        }
        if self.command:
            d["command"] = self.command
        if self.terminal:
            d["terminal"] = self.terminal
        if self.cwd:
            d["cwd"] = self.cwd
        if self.env:
            d["env"] = self.env
        if self.keywords:
            d["keywords"] = self.keywords
        if self.shortcut:
            d["shortcut"] = self.shortcut
        if self.subcommands:
            d["subcommands"] = [sub.to_dict() for sub in self.subcommands]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandItem":
        """Construct a CommandItem from a configuration dictionary."""
        subcommands = [
            cls.from_dict(sub) for sub in data.get("subcommands", []) if isinstance(sub, dict)
        ]
        return cls(
            name=str(data.get("name", "")),
            command=str(data.get("command", "")),
            description=str(data.get("description", "")),
            icon=str(data.get("icon", "utilities-terminal")),
            category=str(data.get("category", "Commands")),
            terminal=bool(data.get("terminal", False)),
            cwd=data.get("cwd"),
            env=data.get("env", {}) if isinstance(data.get("env"), dict) else {},
            subcommands=subcommands,
            keywords=list(data.get("keywords", [])),
            shortcut=str(data.get("shortcut", "")),
        )
