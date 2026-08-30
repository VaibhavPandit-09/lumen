"""
Abstract Base Provider definition for Lumen search providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from lumen.core.logging import error
from lumen.core.models import SearchResult


class BaseProvider(ABC):
    """Abstract interface that all search providers must implement."""

    def __init__(self, name: str, enabled: bool = True):
        self._name = name
        self._enabled = enabled

    @property
    def name(self) -> str:
        """Provider name identifier."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Whether this provider is currently enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def initialize(self) -> None:
        """Called once when provider is loaded into search engine."""
        pass

    def refresh(self) -> None:
        """Called to refresh cached data or index."""
        pass

    def safe_search(self, query: str) -> List[SearchResult]:
        """
        Executes search with strict error boundary protection.
        Prevents any single provider exception from breaking the entire search pipeline.
        """
        if not self._enabled:
            return []
        try:
            results = self.search(query)
            # Annotate origin provider if not set
            for r in results:
                if not r.origin_provider:
                    r.origin_provider = self._name
            return results
        except Exception as e:
            error(f"Provider:{self._name}", f"Search failed on query '{query[:20]}'", exc=e)
            return []

    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """
        Searches the provider for matching items given a query string.
        Should return a list of SearchResult objects with scores.
        """
        raise NotImplementedError
