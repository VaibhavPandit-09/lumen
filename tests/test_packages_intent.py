"""
Unit tests for package intent parsing and PackagesProvider.
"""

import unittest
from unittest.mock import MagicMock, patch

from lumen.core.packages.base import PackageInfo
from lumen.core.packages.intent import CommandIntent, IntentParser, IntentType
from lumen.providers.packages import PackagesProvider


class TestPackagesIntent(unittest.TestCase):
    """Tests intent parsing for natural package manager queries."""

    def test_update_all_intents(self):
        queries = ["update all", "upgrade all", "update system", "upgrade system", "system updates", "updates"]
        for q in queries:
            intent = IntentParser.parse(q)
            self.assertEqual(intent.intent_type, IntentType.UPDATE_ALL, f"Failed for '{q}'")

    def test_install_intents(self):
        queries = [
            ("install htop", "htop"),
            ("add neovim", "neovim"),
            ("get vscode", "vscode"),
            ("i tree", "tree"),
            ("install build-essential", "build-essential"),
        ]
        for q, target in queries:
            intent = IntentParser.parse(q)
            self.assertEqual(intent.intent_type, IntentType.INSTALL, f"Failed for '{q}'")
            self.assertEqual(intent.target, target)

    def test_remove_intents(self):
        queries = [
            ("uninstall firefox", "firefox"),
            ("remove docker", "docker"),
            ("rm vlc", "vlc"),
            ("purge nginx", "nginx"),
        ]
        for q, target in queries:
            intent = IntentParser.parse(q)
            self.assertEqual(intent.intent_type, IntentType.REMOVE, f"Failed for '{q}'")
            self.assertEqual(intent.target, target)

    def test_search_fallback_intent(self):
        intent = IntentParser.parse("calculator")
        self.assertEqual(intent.intent_type, IntentType.SEARCH)
        self.assertEqual(intent.target, "calculator")


class TestPackagesProvider(unittest.TestCase):
    """Tests PackagesProvider search integration."""

    @patch("lumen.core.packages.manager.PackageManager.check_all_updates")
    def test_provider_update_all_intent(self, mock_updates):
        mock_updates.return_value = {
            "APT": [PackageInfo(name="curl", source_backend="apt", update_available=True)],
        }
        provider = PackagesProvider(enabled=True)
        results = provider.search("update all")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Update All Software")
        self.assertEqual(results[0].badge, "System Update")
        self.assertIsNotNone(results[0].payload)

    @patch("lumen.core.packages.manager.PackageManager.search_all")
    def test_provider_install_intent(self, mock_search):
        mock_search.return_value = [
            PackageInfo(name="htop", summary="interactive process viewer", source_backend="apt"),
        ]
        provider = PackagesProvider(enabled=True)
        results = provider.search("install htop")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "htop")
        self.assertEqual(results[0].badge, "APT")
        self.assertIsNotNone(results[0].payload)


if __name__ == "__main__":
    unittest.main()
