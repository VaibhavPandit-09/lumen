"""
Cached currency conversion provider with zero-latency local evaluation.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from lumen.core.logging import debug, warning
from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import copy_to_clipboard
from lumen.providers.base import BaseProvider

# Reference baseline currency rates (EUR base = 1.0)
DEFAULT_CURRENCY_RATES: Dict[str, float] = {
    "EUR": 1.0,
    "USD": 1.08,
    "GBP": 0.85,
    "JPY": 164.5,
    "CAD": 1.48,
    "AUD": 1.66,
    "CHF": 0.96,
    "INR": 90.2,
    "CNY": 7.82,
    "BRL": 5.45,
    "KRW": 1450.0,
    "SEK": 11.4,
    "NOK": 11.6,
    "SGD": 1.46,
    "NZD": 1.78,
}

CURRENCY_SYMBOLS: Dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₩": "KRW",
    "R$": "BRL",
}


class CurrencyProvider(BaseProvider):
    """Provides local cached currency conversions."""

    def __init__(self, enabled: bool = True):
        super().__init__("currency", enabled=enabled)
        self.rates: Dict[str, float] = dict(DEFAULT_CURRENCY_RATES)
        self._cache_file = self._get_cache_path()
        self._load_cache()

    def _get_cache_path(self) -> Path:
        cache_dir = Path(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))) / "lumen"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return cache_dir / "currency_rates.json"

    def _load_cache(self) -> None:
        """Loads cached exchange rates from disk if present."""
        if self._cache_file.is_file():
            try:
                data = json.loads(self._cache_file.read_text(encoding="utf-8"))
                if "rates" in data and isinstance(data["rates"], dict):
                    self.rates.update({k.upper(): float(v) for k, v in data["rates"].items()})
                    debug("Currency", f"Loaded {len(self.rates)} cached currency rates.")
            except Exception as e:
                debug("Currency", f"Could not load currency cache: {e}")

    def parse_query(self, query: str) -> Optional[tuple[float, str, str]]:
        """Parses queries like '100 USD in EUR', '$110 to EUR', '10 EUR = USD'."""
        s = query.strip()

        # Handle leading currency symbol (e.g. $110 to EUR, €50 in USD)
        for sym, code in CURRENCY_SYMBOLS.items():
            if s.startswith(sym):
                rest = s[len(sym):].strip()
                s = f"{rest} {code}"
                # If query was "$110 to EUR", s becomes "110 to EUR USD", so let's handle separator properly
                parts = re.split(r"\s+(?:in|to|=|->|as)\s+", rest, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) == 2:
                    s = f"{parts[0]} {code} in {parts[1]}"
                break

        pattern = r"^\s*([\d\.\-]+)\s*([a-zA-Z]{3})\s+(?:in|to|=|->|as)\s+([a-zA-Z]{3})\s*$"
        m = re.match(pattern, s, re.IGNORECASE)
        if not m:
            return None

        try:
            val = float(m.group(1))
            c_from = m.group(2).upper()
            c_to = m.group(3).upper()
            return val, c_from, c_to
        except ValueError:
            return None

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query:
            return []

        parsed = self.parse_query(query)
        if not parsed:
            return []

        val, c_from, c_to = parsed
        if c_from not in self.rates or c_to not in self.rates:
            return []

        # Convert to EUR base, then to target
        rate_from = self.rates[c_from]
        rate_to = self.rates[c_to]

        eur_val = val / rate_from
        converted = eur_val * rate_to

        formatted_val = f"{converted:,.2f}"
        result_title = f"{val:g} {c_from} = {formatted_val} {c_to}"
        copy_text = f"{formatted_val} {c_to}"

        item = SearchResult(
            id=f"currency:{c_from}:{c_to}",
            title=result_title,
            subtitle=f"Press Enter to copy '{copy_text}' (Currency Conversion)",
            category=ItemCategory.CONVERSION.value,
            icon_name="accessories-calculator",
            score=110.0,
            action=lambda txt=copy_text: copy_to_clipboard(txt),
            badge="Currency",
            origin_provider="currency",
            copy_value=copy_text,
        )

        return [item]
