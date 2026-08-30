"""
Recent files search provider parsing FreeDesktop recently-used.xbel XML.
"""

from __future__ import annotations

import os
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from lumen.core.fuzzy import score_item
from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import open_path_or_url
from lumen.providers.base import BaseProvider


def get_icon_for_mimetype(mime: str) -> str:
    """Maps MIME types to FreeDesktop icon names."""
    if not mime:
        return "text-x-generic"
    if mime.startswith("image/"):
        return "image-x-generic"
    if mime.startswith("video/"):
        return "video-x-generic"
    if mime.startswith("audio/"):
        return "audio-x-generic"
    if "pdf" in mime:
        return "application-pdf"
    if "json" in mime or "xml" in mime or "yaml" in mime:
        return "text-x-script"
    if "python" in mime or "javascript" in mime or "c++" in mime:
        return "text-x-source"
    return "text-x-generic"


class RecentFilesProvider(BaseProvider):
    """Provides searchable recent documents parsed from standard FreeDesktop XBEL store."""

    def __init__(self, enabled: bool = True):
        super().__init__("recent_files", enabled=enabled)
        self.cached_files: List[SearchResult] = []

    def initialize(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        """Parses ~/.local/share/recently-used.xbel."""
        xbel_path = Path.home() / ".local" / "share" / "recently-used.xbel"
        if not xbel_path.exists():
            self.cached_files = []
            return

        results: List[SearchResult] = []
        try:
            tree = ET.parse(str(xbel_path))
            root = tree.getroot()

            # Iterate over <bookmark> elements (most recent last or first)
            for bookmark in root.findall(".//bookmark"):
                href = bookmark.get("href", "")
                if not href.startswith("file://"):
                    continue

                decoded_path = urllib.parse.unquote(href[7:])
                file_path = Path(decoded_path)

                if not file_path.exists():
                    continue

                file_name = file_path.name
                if not file_name:
                    continue

                # Find mime-type
                mime_type = ""
                mime_elem = bookmark.find(".//{http://www.freedesktop.org/standards/shared-mime-info}mime-type")
                if mime_elem is not None:
                    mime_type = mime_elem.get("type", "")

                icon_name = get_icon_for_mimetype(mime_type)

                results.append(
                    SearchResult(
                        id=f"recent:{decoded_path}",
                        title=file_name,
                        subtitle=str(file_path.parent),
                        category=ItemCategory.RECENT.value,
                        icon_name=icon_name,
                        action=lambda p=decoded_path: open_path_or_url(p),
                        badge="Recent",
                        keywords=["recent", "file", file_name, file_path.suffix.lstrip(".")],
                        context={"path": decoded_path, "mime": mime_type},
                    )
                )

            # Reverse so most recent appear first
            self.cached_files = list(reversed(results))[:50]
        except Exception:
            self.cached_files = []

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        results: List[SearchResult] = []
        q = query.strip()

        for item in self.cached_files:
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
                    score=score * 0.9,  # Slight de-boost compared to main apps
                    action=item.action,
                    badge=item.badge,
                    keywords=item.keywords,
                    context=item.context,
                )
                results.append(scored)

        return results
