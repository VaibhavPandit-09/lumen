"""
Common locations search provider (Home, Downloads, Documents, Pictures, Videos, Music, Desktop).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from lumen.core.fuzzy import score_item
from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import open_path_or_url
from lumen.providers.base import BaseProvider


class LocationsProvider(BaseProvider):
    """Provides searchable standard user folders and locations."""

    def __init__(self, enabled: bool = True):
        super().__init__("locations", enabled=enabled)
        self.locations: List[SearchResult] = []

    def initialize(self) -> None:
        home = Path.home()
        raw_locations = [
            ("Home", str(home), "user-home", ["home", "~", "root folder", "files"]),
            ("Downloads", str(home / "Downloads"), "folder-download", ["downloads", "download", "incoming"]),
            ("Documents", str(home / "Documents"), "folder-documents", ["documents", "docs", "papers", "notes"]),
            ("Pictures", str(home / "Pictures"), "folder-pictures", ["pictures", "photos", "images", "pics", "screenshots"]),
            ("Videos", str(home / "Videos"), "folder-videos", ["videos", "movies", "recordings", "clips"]),
            ("Music", str(home / "Music"), "folder-music", ["music", "audio", "songs", "tracks"]),
            ("Desktop", str(home / "Desktop"), "user-desktop", ["desktop", "workspace", "screen"]),
            ("Config Directory", str(home / ".config"), "folder-development", ["config", "settings", "dotfiles"]),
        ]

        self.locations = []
        for name, path_str, icon, kws in raw_locations:
            path = Path(path_str)
            if path.exists() or name in ("Home", "Downloads", "Documents", "Pictures", "Videos", "Music", "Desktop"):
                self.locations.append(
                    SearchResult(
                        id=f"loc:{name.lower()}",
                        title=name,
                        subtitle=path_str,
                        category=ItemCategory.LOCATION.value,
                        icon_name=icon,
                        action=lambda p=path_str: open_path_or_url(p),
                        badge="Folder",
                        keywords=kws,
                        context={"path": path_str},
                    )
                )

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        results: List[SearchResult] = []
        q = query.strip()

        for item in self.locations:
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
                    score=score,
                    action=item.action,
                    badge=item.badge,
                    keywords=item.keywords,
                    context=item.context,
                )
                results.append(scored)

        return results
