"""
Update checker module for discovering new releases.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from lumen import __version__
from lumen.core.logging import debug, error, info
from lumen.core.updater.version import compare_versions


@dataclass
class UpdateInfo:
    """Information about available updates."""
    current_version: str
    latest_version: str
    update_available: bool
    release_url: str = ""
    release_notes: str = ""
    download_url: str = ""
    checksum_url: str = ""
    checked_at: str = ""
    dismissed_until: Optional[str] = None


class UpdateChecker:
    """Checks for new releases on GitHub and caches the result."""

    GITHUB_API_URL = "https://api.github.com/repos/VaibhavPandit-09/lumen/releases/latest"
    CACHE_DIR = Path.home() / ".cache" / "lumen"
    CACHE_FILE = CACHE_DIR / "update_check.json"
    DEFAULT_INTERVAL = 24 * 3600
    MAX_BACKOFF = 7 * 24 * 3600

    def check_for_update(self, force: bool = False) -> Optional[UpdateInfo]:
        """
        Check for available updates. Caches the result to avoid frequent requests.
        """
        cached = self._load_cache()

        if not force and cached and self._is_cache_fresh(self.DEFAULT_INTERVAL):
            return cached

        req = urllib.request.Request(
            self.GITHUB_API_URL,
            headers={"User-Agent": f"Lumen/{__version__}"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            tag_name = data.get("tag_name", "").lstrip("vV")
            html_url = data.get("html_url", "")
            body = data.get("body", "")
            
            download_url = ""
            checksum_url = ""
            
            for asset in data.get("assets", []):
                asset_name = asset.get("name", "")
                if asset_name.endswith(".tar.gz"):
                    download_url = asset.get("browser_download_url", "")
                elif asset_name == "SHA256SUMS":
                    checksum_url = asset.get("browser_download_url", "")

            update_available = compare_versions(tag_name, __version__) > 0

            info_obj = UpdateInfo(
                current_version=__version__,
                latest_version=tag_name,
                update_available=update_available,
                release_url=html_url,
                release_notes=body,
                download_url=download_url,
                checksum_url=checksum_url,
                checked_at=time.strftime("%Y-%m-%dT%H:%M:%S%z")
            )
            
            self._save_cache(info_obj)
            return info_obj
            
        except Exception as e:
            error("UpdateChecker", f"Failed to check for updates: {e}")
            return cached

    def get_cached_update_info(self) -> Optional[UpdateInfo]:
        """Returns currently cached update info without performing network requests."""
        return self._load_cache()

    def _load_cache(self) -> Optional[UpdateInfo]:
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return UpdateInfo(**data)
        except Exception as e:
            debug("UpdateChecker", f"Failed to load update cache: {e}")
        return None

    def _save_cache(self, info: UpdateInfo) -> None:
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(info), f, indent=4)
        except Exception as e:
            error("UpdateChecker", f"Failed to save update cache: {e}")

    def _is_cache_fresh(self, interval_seconds: int) -> bool:
        if not self.CACHE_FILE.exists():
            return False
        return (time.time() - self.CACHE_FILE.stat().st_mtime) < interval_seconds

    def dismiss_version(self, version: str) -> None:
        """Dismiss an update notification for a given version."""
        cached = self._load_cache()
        if cached:
            cached.dismissed_until = version
            self._save_cache(cached)

    def is_dismissed(self, info: UpdateInfo) -> bool:
        """Check if an update version has been dismissed by the user."""
        if not info.update_available:
            return False
        return info.dismissed_until == info.latest_version
