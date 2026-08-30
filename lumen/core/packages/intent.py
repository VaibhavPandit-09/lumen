"""
Natural command intent parsing for package management operations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IntentType(str, Enum):
    INSTALL = "install"
    REMOVE = "remove"
    UPDATE_ONE = "update_one"
    UPDATE_ALL = "update_all"
    LIST_UPDATES = "list_updates"
    SEARCH = "search"
    NONE = "none"


@dataclass
class CommandIntent:
    intent_type: IntentType
    target: str = ""
    backend: Optional[str] = None  # Optional specific backend (e.g. 'flatpak', 'apt')
    raw_query: str = ""


class IntentParser:
    """Parses natural software management queries into structured CommandIntents."""

    _UPDATE_ALL_PATTERNS = [
        r"^(?:update\s+all|upgrade\s+all|update\s+system|upgrade\s+system|system\s+updates|updates)$",
    ]

    _INSTALL_PATTERNS = [
        r"^(?:install|add|get|i)\s+([a-zA-Z0-9_\-\.\+]+)$",
    ]

    _REMOVE_PATTERNS = [
        r"^(?:uninstall|remove|rm|purge|delete)\s+([a-zA-Z0-9_\-\.\+]+)$",
    ]

    _UPDATE_ONE_PATTERNS = [
        r"^(?:update|upgrade)\s+([a-zA-Z0-9_\-\.\+]+)$",
    ]

    @classmethod
    def parse(cls, query: str) -> CommandIntent:
        q = query.strip()
        if not q:
            return CommandIntent(intent_type=IntentType.NONE, raw_query=q)

        # Check for update all / updates
        for pat in cls._UPDATE_ALL_PATTERNS:
            if re.match(pat, q, re.IGNORECASE):
                return CommandIntent(intent_type=IntentType.UPDATE_ALL, raw_query=q)

        # Check for install
        for pat in cls._INSTALL_PATTERNS:
            m = re.match(pat, q, re.IGNORECASE)
            if m:
                target = m.group(1)
                return CommandIntent(intent_type=IntentType.INSTALL, target=target, raw_query=q)

        # Check for remove/uninstall
        for pat in cls._REMOVE_PATTERNS:
            m = re.match(pat, q, re.IGNORECASE)
            if m:
                target = m.group(1)
                return CommandIntent(intent_type=IntentType.REMOVE, target=target, raw_query=q)

        # Check for update specific package
        for pat in cls._UPDATE_ONE_PATTERNS:
            m = re.match(pat, q, re.IGNORECASE)
            if m:
                target = m.group(1)
                if target.lower() not in ("all", "system"):
                    return CommandIntent(intent_type=IntentType.UPDATE_ONE, target=target, raw_query=q)

        return CommandIntent(intent_type=IntentType.SEARCH, target=q, raw_query=q)
