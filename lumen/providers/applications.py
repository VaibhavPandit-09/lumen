"""
Applications search provider discovering FreeDesktop .desktop applications.
"""

from __future__ import annotations

from typing import List, Optional

from lumen.core.app_scanner import AppScanner
from lumen.core.fuzzy import score_item
from lumen.core.models import SearchResult
from lumen.providers.base import BaseProvider


class ApplicationProvider(BaseProvider):
    """Searches installed desktop applications."""

    def __init__(self, hidden_applications: Optional[List[str]] = None, enabled: bool = True):
        super().__init__("applications", enabled=enabled)
        self.scanner = AppScanner(hidden_applications=hidden_applications)

    def initialize(self) -> None:
        self.scanner.scan()
        self.scanner.setup_watcher()

    def refresh(self) -> None:
        self.scanner.scan()

    def set_hidden_applications(self, hidden: List[str]) -> None:
        self.scanner.set_hidden_applications(hidden)
        self.refresh()

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        results: List[SearchResult] = []
        q = query.strip()

        for item in self.scanner.cached_results:
            matched, score = score_item(
                query=q,
                title=item.title,
                subtitle=item.subtitle,
                keywords=item.keywords,
                category=item.category,
            )
            if matched and score > 0:
                # Clone result with updated score
                scored_result = SearchResult(
                    id=item.id,
                    title=item.title,
                    subtitle=item.subtitle,
                    category=item.category,
                    icon_name=item.icon_name,
                    score=score,
                    action=item.action,
                    subcommands=item.subcommands,
                    badge=item.badge,
                    keywords=item.keywords,
                    shortcut_hint=item.shortcut_hint,
                    context=item.context,
                )
                results.append(scored_result)

        return results
