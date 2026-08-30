from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from lumen.core.config import LumenConfig
from lumen.core.models import SearchResult
from lumen.ui.launcher_window import LauncherWindow
from lumen.ui.navigation import NavigationLevel


class TestEscapeHierarchy(unittest.TestCase):
    """Headless UI tests for Escape key hierarchy in LauncherWindow."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.app.setApplicationName("lumen")
        cls.app.setOrganizationName("lumen")

    def setUp(self) -> None:
        self.config = LumenConfig()
        self.window = LauncherWindow(config=self.config)
        self.window.show()

    def tearDown(self) -> None:
        self.window.close()

    def test_escape_cancels_pending_confirmation(self) -> None:
        pending_item = SearchResult(
            id="test:dangerous",
            title="Dangerous Action",
            requires_confirmation=True,
            confirm_prompt="Proceed with dangerous action?",
        )
        self.window._pending_confirmation = pending_item
        self.window._update_breadcrumb()

        self.window._on_escape_pressed()

        self.assertIsNone(self.window._pending_confirmation)
        self.assertTrue(self.window.isVisible())

    def test_escape_pops_submenu(self) -> None:
        sub_items = [
            SearchResult(id="test:sub1", title="Sub Item 1"),
            SearchResult(id="test:sub2", title="Sub Item 2"),
        ]
        self.window.push_submenu("Submenu Title", sub_items)
        self.assertEqual(len(self.window.nav_stack), 1)

        self.window._on_escape_pressed()

        self.assertEqual(len(self.window.nav_stack), 0)
        self.assertTrue(self.window.isVisible())

    def test_escape_pops_navigation_level(self) -> None:
        level = NavigationLevel(title="Apps", provider_filter="applications")
        self.window.nav_manager.push(level)
        self.assertFalse(self.window.nav_manager.is_at_root())

        self.window._on_escape_pressed()

        self.assertTrue(self.window.nav_manager.is_at_root())
        self.assertTrue(self.window.isVisible())

    def test_escape_clears_search_text(self) -> None:
        self.window.search_bar.setText("sample search text")
        self.assertEqual(self.window.search_bar.text(), "sample search text")

        self.window._on_escape_pressed()

        self.assertEqual(self.window.search_bar.text(), "")
        self.assertTrue(self.window.isVisible())

    def test_escape_at_root_dismisses(self) -> None:
        self.assertIsNone(self.window._pending_confirmation)
        self.assertEqual(len(self.window.nav_stack), 0)
        self.assertTrue(self.window.nav_manager.is_at_root())
        self.assertEqual(self.window.search_bar.text(), "")

        with patch.object(self.window, "dismiss") as mock_dismiss:
            self.window._on_escape_pressed()
            mock_dismiss.assert_called_once()

    def test_full_nested_escape_sequence(self) -> None:
        # Layer 1: Search text
        self.window.search_bar.setText("sample query")

        # Layer 2: Navigation level
        self.window.nav_manager.push(NavigationLevel(title="Packages", provider_filter="packages"))

        # Layer 3: Submenu
        sub_items = [SearchResult(id="pkg:opt", title="Options")]
        self.window.push_submenu("Package Actions", sub_items)

        # Layer 4: Pending confirmation
        pending_item = SearchResult(
            id="pkg:confirm",
            title="Confirm Install",
            requires_confirmation=True,
        )
        self.window._pending_confirmation = pending_item

        # Initial state check
        self.assertIsNotNone(self.window._pending_confirmation)
        self.assertEqual(len(self.window.nav_stack), 1)
        self.assertFalse(self.window.nav_manager.is_at_root())
        self.assertTrue(self.window.isVisible())

        # Escape step 1: Cancels pending confirmation
        self.window._on_escape_pressed()
        self.assertIsNone(self.window._pending_confirmation)
        self.assertEqual(len(self.window.nav_stack), 1)
        self.assertFalse(self.window.nav_manager.is_at_root())
        self.assertTrue(self.window.isVisible())

        # Escape step 2: Pops submenu
        self.window._on_escape_pressed()
        self.assertIsNone(self.window._pending_confirmation)
        self.assertEqual(len(self.window.nav_stack), 0)
        self.assertFalse(self.window.nav_manager.is_at_root())
        self.assertTrue(self.window.isVisible())

        # Escape step 3: Pops navigation level
        self.window._on_escape_pressed()
        self.assertIsNone(self.window._pending_confirmation)
        self.assertEqual(len(self.window.nav_stack), 0)
        self.assertTrue(self.window.nav_manager.is_at_root())
        self.assertTrue(self.window.isVisible())

        # Set search text at root to test search text clearing step
        self.window.search_bar.setText("root search query")
        self.assertEqual(self.window.search_bar.text(), "root search query")

        # Escape step 4: Clears search text
        self.window._on_escape_pressed()
        self.assertEqual(self.window.search_bar.text(), "")
        self.assertTrue(self.window.nav_manager.is_at_root())
        self.assertTrue(self.window.isVisible())

        # Escape step 5: Dismisses launcher at root
        with patch.object(self.window, "dismiss") as mock_dismiss:
            self.window._on_escape_pressed()
            mock_dismiss.assert_called_once()


if __name__ == "__main__":
    unittest.main()
