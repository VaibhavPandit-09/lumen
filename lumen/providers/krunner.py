"""
Optional KRunner provider adapter integrating with KDE Plasma 6 KRunner runners via D-Bus.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional

from lumen.core.logging import debug, error, info
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.base import BaseProvider

try:
    from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage
    HAS_QT_DBUS = True
except ImportError:
    HAS_QT_DBUS = False


class KRunnerProvider(BaseProvider):
    """
    Optional KRunner integration adapter for KDE Plasma.
    Queries KRunner services via D-Bus when available, degrading gracefully when offline.
    """

    def __init__(self, enabled: bool = True):
        super().__init__("krunner", enabled=enabled)
        self._available: Optional[bool] = None

    def initialize(self) -> None:
        self._check_availability()

    def _check_availability(self) -> bool:
        """Checks if KDE KRunner D-Bus service is responsive."""
        if not HAS_QT_DBUS:
            self._available = False
            return False

        try:
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                self._available = False
                return False

            # Check if org.kde.krunner is available in registered names
            iface = QDBusInterface("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", bus)
            if iface.isValid():
                reply = iface.call("ListNames")
                if reply.arguments():
                    names = reply.arguments()[0]
                    self._available = any("krunner" in name.lower() for name in names)
                    debug("KRunner", f"D-Bus probe: available={self._available}")
                    return bool(self._available)
        except Exception as e:
            debug("KRunner", f"Availability check exception: {e}")

        self._available = False
        return False

    @property
    def is_available(self) -> bool:
        if self._available is None:
            return self._check_availability()
        return self._available

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query or len(query.strip()) < 2:
            return []

        if not self.is_available:
            return []

        # If available, query KRunner runner service
        results: List[SearchResult] = []
        try:
            bus = QDBusConnection.sessionBus()
            iface = QDBusInterface("org.kde.krunner", "/App", "org.kde.krunner.App", bus)
            if iface.isValid():
                # Call KRunner query if exposed
                reply = iface.call("query", query)
                # Parse query reply if structured matches returned
                debug("KRunner", f"Query returned: {reply}")
        except Exception as e:
            debug("KRunner", f"Query failed ({e})")

        return results
