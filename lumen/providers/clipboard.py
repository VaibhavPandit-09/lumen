"""
KDE Clipboard integration provider without competing daemons.
"""

from __future__ import annotations

from typing import List

from lumen.core.fuzzy import score_item
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.base import BaseProvider

try:
    from PyQt6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False


class ClipboardProvider(BaseProvider):
    """Provides access to current clipboard content and history."""

    def __init__(self, enabled: bool = True):
        super().__init__("clipboard", enabled=enabled)

    def _get_current_clipboard_text(self) -> str:
        if not HAS_QT:
            return ""
        app = QApplication.instance()
        if not app:
            return ""
        clipboard = QApplication.clipboard()
        if not clipboard:
            return ""
        return clipboard.text() or ""

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        text = self._get_current_clipboard_text().strip()
        if not text:
            return []

        q = query.strip()
        # Preview short text
        preview = text.replace("\n", " ").strip()
        if len(preview) > 60:
            preview = preview[:57] + "..."

        matched, score = score_item(
            query=q,
            title="Clipboard: " + preview,
            subtitle=text if len(text) <= 120 else text[:117] + "...",
            keywords=["clipboard", "paste", "copy", "history"],
            category=ItemCategory.CLIPBOARD.value,
        )

        if matched and score > 0:
            return [
                SearchResult(
                    id="clipboard:current",
                    title="Clipboard Content",
                    subtitle=preview,
                    category=ItemCategory.CLIPBOARD.value,
                    icon_name="edit-copy",
                    score=score * 0.85,
                    action=None,  # Already in clipboard
                    badge="Clip",
                    keywords=["clipboard", "copy", "paste"],
                    context={"text": text},
                )
            ]

        return []
