"""
Search provider for physical, time, and data size unit conversions.
"""

from __future__ import annotations

from typing import List

from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import copy_to_clipboard
from lumen.core.units import parse_and_convert_unit
from lumen.providers.base import BaseProvider


class ConversionsProvider(BaseProvider):
    """Provides instant physical and data unit conversions."""

    def __init__(self, enabled: bool = True):
        super().__init__("conversions", enabled=enabled)

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query:
            return []

        conv = parse_and_convert_unit(query)
        if not conv:
            return []

        # Extract right-hand side value for clipboard copying
        copy_text = conv.formatted_result.split("=")[-1].strip()

        result_item = SearchResult(
            id="conversion:unit",
            title=conv.formatted_result,
            subtitle=f"Press Enter to copy '{copy_text}' ({conv.category})",
            category=ItemCategory.CONVERSION.value,
            icon_name="accessories-calculator",
            score=110.0,
            action=lambda txt=copy_text: copy_to_clipboard(txt),
            badge="Unit",
            origin_provider="conversions",
            copy_value=copy_text,
        )

        return [result_item]
