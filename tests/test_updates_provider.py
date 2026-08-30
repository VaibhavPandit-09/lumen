"""
Unit tests for UpdatesProvider handling Lumen self-updates and system software updates.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from lumen import __version__
from lumen.core.actions.dispatcher import ActionType
from lumen.core.packages.base import PackageInfo, PackageOperationResult
from lumen.core.updater.checker import UpdateInfo
from lumen.core.updater.installer import UpdateResult
from lumen.providers.updates import UpdatesProvider


class TestUpdatesProvider(unittest.TestCase):
    """Unit tests for UpdatesProvider."""

    def setUp(self) -> None:
        self.provider = UpdatesProvider()

    def test_provider_initialization(self) -> None:
        """Verify provider name and initial state."""
        self.assertEqual(self.provider.name, "UpdatesProvider")
        self.assertTrue(self.provider.enabled)
        self.assertIsNone(self.provider.manager)
        self.assertIsNone(self.provider.checker)
        self.assertIsNone(self.provider._cached_lumen_update)

        mock_mgr = MagicMock()
        mock_checker = MagicMock()
        mock_checker._load_cache.return_value = None

        with patch("lumen.core.packages.manager.PackageManager.get_instance", return_value=mock_mgr), \
             patch("lumen.providers.updates.UpdateChecker", return_value=mock_checker):
            self.provider.initialize()
            self.assertEqual(self.provider.manager, mock_mgr)
            self.assertEqual(self.provider.checker, mock_checker)

            # Test refresh calls initialize
            self.provider.refresh()
            self.assertEqual(self.provider.manager, mock_mgr)

    def test_lumen_update_item_when_available(self) -> None:
        """Mock cached UpdateInfo with update_available=True, search(''), verify Lumen update SearchResult is returned."""
        info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            release_notes="Brand new features and improvements",
        )

        mock_checker = MagicMock()
        mock_checker.is_dismissed.return_value = False
        mock_checker._load_cache.return_value = info

        mock_manager = MagicMock()
        mock_manager.check_all_updates.return_value = {}

        self.provider.checker = mock_checker
        self.provider.manager = mock_manager
        self.provider._cached_lumen_update = info

        results = self.provider.search("")
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result.id, "update:lumen_self")
        self.assertEqual(result.title, "Update Lumen to v0.6.0")
        self.assertIn("v0.5.0 → v0.6.0", result.subtitle)
        self.assertIn("Brand new features", result.subtitle)
        self.assertEqual(result.badge, "Lumen Update")
        self.assertEqual(result.score, 100.0)

        # Verify action payload and execution
        self.assertIsNotNone(result.payload)
        self.assertEqual(result.payload.action_type, ActionType.LUMEN_INTERNAL)
        self.assertEqual(result.payload.target, "self_update")
        self.assertTrue(result.payload.is_async)

        with patch("lumen.providers.updates.SelfUpdater.update") as mock_update:
            mock_update.return_value = UpdateResult(success=True, message="Update successful", new_version="0.6.0")
            update_res = result.payload.handler()
            mock_update.assert_called_once_with(info)
            self.assertTrue(update_res.success)

    def test_system_updates_items(self) -> None:
        """Mock PackageManager.check_all_updates with APT updates, search(''), verify 'Update All' and backend items returned."""
        mock_manager = MagicMock()
        apt_packages = [
            PackageInfo(name="ripgrep", version="14.1.0", source_backend="apt", installed=True),
            PackageInfo(name="curl", version="8.5.0", source_backend="apt", installed=True),
        ]
        mock_manager.check_all_updates.return_value = {"APT": apt_packages}

        mock_backend = MagicMock()
        mock_backend.update.return_value = PackageOperationResult(success=True, message="APT packages updated")
        mock_manager.get_backend.return_value = mock_backend
        mock_manager.update_all.return_value = {"APT": PackageOperationResult(success=True, message="APT updated")}

        self.provider.manager = mock_manager
        self.provider._cached_lumen_update = None
        self.provider.checker = None

        results = self.provider.search("")
        self.assertEqual(len(results), 2)

        # 1. Update All meta-item
        update_all = results[0]
        self.assertEqual(update_all.id, "update:all_system")
        self.assertEqual(update_all.title, "Update All System Software")
        self.assertIn("2 pending updates", update_all.subtitle)
        self.assertEqual(update_all.badge, "Update All")
        self.assertEqual(update_all.payload.action_type, ActionType.SYSTEM_UPDATE_ALL)

        # Test Update All execution handler
        res_all = update_all.payload.handler()
        self.assertTrue(res_all.success)
        mock_manager.update_all.assert_called_once()

        # 2. Per-backend item
        backend_item = results[1]
        self.assertEqual(backend_item.id, "update:backend:apt")
        self.assertEqual(backend_item.title, "Update APT Software")
        self.assertIn("ripgrep, curl", backend_item.subtitle)
        self.assertEqual(backend_item.badge, "APT")
        self.assertEqual(backend_item.payload.action_type, ActionType.PACKAGE_UPDATE)

        # Test per-backend execution handler
        res_backend = backend_item.payload.handler()
        self.assertTrue(res_backend.success)
        mock_backend.update.assert_called_once()

    def test_empty_state_when_no_updates(self) -> None:
        """Mock no updates, search('updates'), verify 'All software is up to date' empty state result."""
        mock_manager = MagicMock()
        mock_manager.check_all_updates.return_value = {}

        self.provider.manager = mock_manager
        self.provider._cached_lumen_update = None
        self.provider.checker = None

        # When searching 'updates'
        results = self.provider.search("updates")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "update:all_current")
        self.assertEqual(results[0].title, "All software is up to date")
        self.assertTrue(results[0].is_empty_state)
        self.assertEqual(results[0].badge, "Up to date")
        self.assertIn(f"Lumen v{__version__}", results[0].subtitle)

        # When searching empty string ""
        results_empty = self.provider.search("")
        self.assertEqual(len(results_empty), 1)
        self.assertEqual(results_empty[0].id, "update:all_current")
        self.assertTrue(results_empty[0].is_empty_state)

    def test_search_query_filtering(self) -> None:
        """Query 'apt', verify only matching updates returned."""
        info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            release_notes="Release 0.6.0",
        )
        mock_checker = MagicMock()
        mock_checker.is_dismissed.return_value = False
        mock_checker._load_cache.return_value = info

        mock_manager = MagicMock()
        apt_packages = [
            PackageInfo(name="ripgrep", version="14.1.0", source_backend="apt", installed=True),
        ]
        mock_manager.check_all_updates.return_value = {"APT": apt_packages}

        self.provider.checker = mock_checker
        self.provider.manager = mock_manager
        self.provider._cached_lumen_update = info

        # Query "apt" does not match Lumen update keywords ("lumen", "update", "self", or "")
        # but returns system update items
        results = self.provider.search("apt")
        result_ids = [r.id for r in results]
        self.assertNotIn("update:lumen_self", result_ids)
        self.assertIn("update:all_system", result_ids)
        self.assertIn("update:backend:apt", result_ids)

        # Query "lumen" returns Lumen update item
        results_lumen = self.provider.search("lumen")
        lumen_ids = [r.id for r in results_lumen]
        self.assertIn("update:lumen_self", lumen_ids)

        # Query completely unrelated term when no updates match
        mock_manager.check_all_updates.return_value = {}
        self.provider._cached_lumen_update = None
        results_unrelated = self.provider.search("unrelated_search_term")
        self.assertEqual(results_unrelated, [])

        # Disabled provider returns empty list
        self.provider.enabled = False
        self.assertEqual(self.provider.search(""), [])


if __name__ == "__main__":
    unittest.main()
