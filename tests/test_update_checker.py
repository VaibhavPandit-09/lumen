"""
Unit tests for the update checker subsystem and UpdateInfo dataclass.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from lumen import __version__
from lumen.core.updater.checker import UpdateChecker, UpdateInfo


class TestUpdateChecker(unittest.TestCase):
    """Unit tests for UpdateChecker and UpdateInfo."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)
        self.cache_file = self.cache_dir / "update_check.json"

        self.checker = UpdateChecker()
        self.checker.CACHE_DIR = self.cache_dir
        self.checker.CACHE_FILE = self.cache_file

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_update_info_dataclass(self) -> None:
        """Verify UpdateInfo fields and default values."""
        info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
        )
        self.assertEqual(info.current_version, "0.5.0")
        self.assertEqual(info.latest_version, "0.6.0")
        self.assertTrue(info.update_available)
        self.assertEqual(info.release_url, "")
        self.assertEqual(info.release_notes, "")
        self.assertEqual(info.download_url, "")
        self.assertEqual(info.checksum_url, "")
        self.assertEqual(info.checked_at, "")
        self.assertIsNone(info.dismissed_until)

        full_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            release_url="https://github.com/example/release",
            release_notes="Fixes and improvements",
            download_url="https://github.com/example/lumen.tar.gz",
            checksum_url="https://github.com/example/SHA256SUMS",
            checked_at="2026-08-30T12:00:00Z",
            dismissed_until="0.6.0",
        )
        self.assertEqual(full_info.release_url, "https://github.com/example/release")
        self.assertEqual(full_info.release_notes, "Fixes and improvements")
        self.assertEqual(full_info.download_url, "https://github.com/example/lumen.tar.gz")
        self.assertEqual(full_info.checksum_url, "https://github.com/example/SHA256SUMS")
        self.assertEqual(full_info.checked_at, "2026-08-30T12:00:00Z")
        self.assertEqual(full_info.dismissed_until, "0.6.0")

    def test_cache_save_and_load(self) -> None:
        """Save to temporary CACHE_FILE, load, and verify fields match."""
        info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            release_url="https://github.com/example/release",
            release_notes="Release notes here",
            download_url="https://github.com/example/lumen.tar.gz",
            checksum_url="https://github.com/example/SHA256SUMS",
            checked_at="2026-08-30T12:00:00Z",
            dismissed_until=None,
        )
        self.checker._save_cache(info)
        self.assertTrue(self.cache_file.exists())

        loaded = self.checker._load_cache()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded, info)
        self.assertEqual(self.checker.get_cached_update_info(), info)

    def test_cache_freshness(self) -> None:
        """Verify _is_cache_fresh returns True within interval, False after."""
        # Non-existent cache file
        self.assertFalse(self.checker._is_cache_fresh(3600))

        # Fresh cache file
        info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
        )
        self.checker._save_cache(info)
        self.assertTrue(self.checker._is_cache_fresh(3600))

        # Stale cache file (set mtime to 2 hours ago)
        past_time = time.time() - 7200
        os.utime(self.cache_file, (past_time, past_time))
        self.assertFalse(self.checker._is_cache_fresh(3600))

    @patch("urllib.request.urlopen")
    def test_check_for_update_newer_version(self, mock_urlopen: MagicMock) -> None:
        """Mock urllib.request.urlopen returning GitHub release JSON with v99.0.0, verify update_available=True, asset URLs parsed."""
        payload = {
            "tag_name": "v99.0.0",
            "html_url": "https://github.com/VaibhavPandit-09/lumen/releases/tag/v99.0.0",
            "body": "Major new release features.",
            "assets": [
                {
                    "name": "lumen-99.0.0.tar.gz",
                    "browser_download_url": "https://github.com/VaibhavPandit-09/lumen/releases/download/v99.0.0/lumen-99.0.0.tar.gz",
                },
                {
                    "name": "SHA256SUMS",
                    "browser_download_url": "https://github.com/VaibhavPandit-09/lumen/releases/download/v99.0.0/SHA256SUMS",
                },
            ],
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        info = self.checker.check_for_update(force=True)
        self.assertIsNotNone(info)
        self.assertTrue(info.update_available)
        self.assertEqual(info.latest_version, "99.0.0")
        self.assertEqual(info.current_version, __version__)
        self.assertEqual(
            info.release_url,
            "https://github.com/VaibhavPandit-09/lumen/releases/tag/v99.0.0",
        )
        self.assertEqual(info.release_notes, "Major new release features.")
        self.assertEqual(
            info.download_url,
            "https://github.com/VaibhavPandit-09/lumen/releases/download/v99.0.0/lumen-99.0.0.tar.gz",
        )
        self.assertEqual(
            info.checksum_url,
            "https://github.com/VaibhavPandit-09/lumen/releases/download/v99.0.0/SHA256SUMS",
        )

    @patch("urllib.request.urlopen")
    def test_check_for_update_same_version(self, mock_urlopen: MagicMock) -> None:
        """Mock release with current version, verify update_available=False."""
        payload = {
            "tag_name": f"v{__version__}",
            "html_url": f"https://github.com/VaibhavPandit-09/lumen/releases/tag/v{__version__}",
            "body": "Current version release notes",
            "assets": [],
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        info = self.checker.check_for_update(force=True)
        self.assertIsNotNone(info)
        self.assertFalse(info.update_available)
        self.assertEqual(info.latest_version, __version__)

    @patch("urllib.request.urlopen")
    def test_check_for_update_network_error(self, mock_urlopen: MagicMock) -> None:
        """Mock urlopen raising URLError, verify graceful fallback to cached info."""
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

        # Case 1: No cached info
        info = self.checker.check_for_update(force=True)
        self.assertIsNone(info)

        # Case 2: Cached info available
        cached_info = UpdateInfo(
            current_version=__version__,
            latest_version="99.0.0",
            update_available=True,
            release_url="https://github.com/example/release",
        )
        self.checker._save_cache(cached_info)

        fallback_info = self.checker.check_for_update(force=True)
        self.assertIsNotNone(fallback_info)
        self.assertEqual(fallback_info, cached_info)

    def test_dismiss_version(self) -> None:
        """Call dismiss_version('0.6.0'), verify is_dismissed returns True for 0.6.0 and False for 0.7.0."""
        cached_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
        )
        self.checker._save_cache(cached_info)

        self.checker.dismiss_version("0.6.0")

        # Reload cached info to inspect modified dismissed_until
        updated_cached = self.checker.get_cached_update_info()
        self.assertIsNotNone(updated_cached)
        self.assertEqual(updated_cached.dismissed_until, "0.6.0")

        # Test is_dismissed for 0.6.0
        self.assertTrue(self.checker.is_dismissed(updated_cached))

        # Test is_dismissed for 0.7.0
        newer_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.7.0",
            update_available=True,
            dismissed_until="0.6.0",
        )
        self.assertFalse(self.checker.is_dismissed(newer_info))

        # Test is_dismissed when update_available is False
        no_update_info = UpdateInfo(
            current_version="0.6.0",
            latest_version="0.6.0",
            update_available=False,
            dismissed_until="0.6.0",
        )
        self.assertFalse(self.checker.is_dismissed(no_update_info))


if __name__ == "__main__":
    unittest.main()
