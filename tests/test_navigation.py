from __future__ import annotations

import unittest

from lumen.core.models import SearchResult
from lumen.ui.navigation import NavigationLevel, NavigationManager


class TestNavigation(unittest.TestCase):
    """Tests for lumen.ui.navigation components."""

    def test_navigation_level_creation(self) -> None:
        # Test with default values
        level_default = NavigationLevel(title="Default Level")
        self.assertEqual(level_default.title, "Default Level")
        self.assertEqual(level_default.items, [])
        self.assertEqual(level_default.search_query, "")
        self.assertIsNone(level_default.provider_filter)
        self.assertEqual(level_default.placeholder_text, "Type to search...")
        self.assertEqual(level_default.icon_name, "system-search")

        # Test with custom values
        items = [SearchResult(id="item:1", title="Test Item")]
        level_custom = NavigationLevel(
            title="Custom Level",
            items=items,
            search_query="query",
            provider_filter="apps",
            placeholder_text="Search custom...",
            icon_name="custom-icon",
        )
        self.assertEqual(level_custom.title, "Custom Level")
        self.assertEqual(level_custom.items, items)
        self.assertEqual(level_custom.search_query, "query")
        self.assertEqual(level_custom.provider_filter, "apps")
        self.assertEqual(level_custom.placeholder_text, "Search custom...")
        self.assertEqual(level_custom.icon_name, "custom-icon")

    def test_navigation_manager_initial_state(self) -> None:
        nav = NavigationManager()
        self.assertTrue(nav.is_at_root())
        self.assertEqual(nav.depth(), 0)
        self.assertEqual(nav.breadcrumb_path(), "")
        self.assertIsNone(nav.current_level())

    def test_push_and_pop(self) -> None:
        nav = NavigationManager()
        level = NavigationLevel(title="Apps", provider_filter="applications")

        nav.push(level)
        self.assertFalse(nav.is_at_root())
        self.assertEqual(nav.depth(), 1)
        self.assertEqual(nav.current_level(), level)
        self.assertEqual(nav.breadcrumb_path(), "Lumen › Apps")

        popped = nav.pop()
        self.assertEqual(popped, level)
        self.assertTrue(nav.is_at_root())
        self.assertEqual(nav.depth(), 0)
        self.assertIsNone(nav.current_level())
        self.assertEqual(nav.breadcrumb_path(), "")

    def test_pop_empty(self) -> None:
        nav = NavigationManager()
        self.assertIsNone(nav.pop())
        self.assertTrue(nav.is_at_root())
        self.assertEqual(nav.depth(), 0)

    def test_reset(self) -> None:
        nav = NavigationManager()
        nav.push(NavigationLevel(title="Level 1"))
        nav.push(NavigationLevel(title="Level 2"))
        nav.push(NavigationLevel(title="Level 3"))
        self.assertEqual(nav.depth(), 3)
        self.assertFalse(nav.is_at_root())

        nav.reset()
        self.assertTrue(nav.is_at_root())
        self.assertEqual(nav.depth(), 0)
        self.assertIsNone(nav.current_level())
        self.assertEqual(nav.breadcrumb_path(), "")

    def test_root_categories(self) -> None:
        nav = NavigationManager()
        root_categories = nav.get_root_categories()
        titles = [cat.title for cat in root_categories]
        expected_titles = ["Apps", "Packages", "Updates", "Commands", "Files", "System"]
        for expected in expected_titles:
            self.assertIn(expected, titles)
        self.assertEqual(len(root_categories), 6)

    def test_breadcrumb_path_multiple(self) -> None:
        nav = NavigationManager()
        nav.push(NavigationLevel(title="Level1"))
        nav.push(NavigationLevel(title="Level2"))
        nav.push(NavigationLevel(title="Level3"))
        self.assertEqual(nav.breadcrumb_path(), "Lumen › Level1 › Level2 › Level3")


if __name__ == "__main__":
    unittest.main()
