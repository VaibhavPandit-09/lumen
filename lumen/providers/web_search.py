"""
Fallback web search provider opening queries in the user's default browser.
"""

from __future__ import annotations

import urllib.parse
from typing import List

from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import open_path_or_url
from lumen.providers.base import BaseProvider


class WebSearchProvider(BaseProvider):
    """Provides fallback web search action for queries."""

    def __init__(
        self,
        engine_template: str = "https://duckduckgo.com/?q=%s",
        enabled: bool = True,
    ):
        super().__init__("web_search", enabled=enabled)
        self.engine_template = engine_template

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query:
            return []

        q = query.strip()
        if len(q) < 2:
            return []

        encoded = urllib.parse.quote_plus(q)
        url = self.engine_template.replace("%s", encoded)

        return [
            SearchResult(
                id=f"web:{encoded}",
                title=f'Search "{q}" on the web',
                subtitle="Open search query in default web browser",
                category=ItemCategory.WEB.value,
                icon_name="globe",
                score=1.0,  # Fallback lowest score
                action=lambda target_url=url: open_path_or_url(target_url),
                badge="Web",
                keywords=["web", "search", "google", "duckduckgo", "browser", "internet"],
                context={"url": url, "query": q},
            )
        ]
