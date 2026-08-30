"""
Abstract Base Provider definition for Lumen search providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

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

    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """
        Searches the provider for matching items given a query string.
        Should return a list of SearchResult objects with scores.
        """
        raise NotImplementedError
