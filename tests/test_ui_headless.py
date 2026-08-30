"""
Headless UI tests for LauncherWindow and ResultListWidget.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from lumen.core.config import LumenConfig
from lumen.core.models import SearchResult
from lumen.ui.launcher_window import LauncherWindow


class TestUIHeadless(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.config = LumenConfig()
        self.window = LauncherWindow(config=self.config)

    def tearDown(self):
        self.window.close()

    def test_window_initialization(self):
        self.assertIsNotNone(self.window.search_bar)
        self.assertIsNotNone(self.window.result_list)
        self.assertEqual(self.window.minimumWidth(), self.config.window_width)

    def test_search_and_result_population(self):
        # Math query
        self.window.update_results("12 * 12")
        self.assertGreater(self.window.result_list.count(), 0)
        top_item: SearchResult = self.window.result_list.item(0).data(0x0100)  # UserRole
        self.assertEqual(top_item.title, "= 144")

        # System query
        self.window.update_results("lock")
        self.assertGreater(self.window.result_list.count(), 0)
        found_lock = False
        for i in range(self.window.result_list.count()):
            res = self.window.result_list.item(i).data(0x0100)
            if res and "Lock" in res.title:
                found_lock = True
                break
        self.assertTrue(found_lock)

    def test_submenu_navigation_stack(self):
        sub_items = [
            SearchResult(id="test:1", title="Sub Item 1"),
            SearchResult(id="test:2", title="Sub Item 2"),
        ]
        self.window.push_submenu("Test Menu", sub_items)
        self.assertEqual(len(self.window.nav_stack), 1)
        self.assertFalse(self.window.breadcrumb_label.isHidden())
        self.assertEqual(self.window.result_list.count(), 2)

        # Pop
        self.window.pop_submenu()
        self.assertEqual(len(self.window.nav_stack), 0)
        self.assertTrue(self.window.breadcrumb_label.isHidden())

    def test_toggle_and_dismiss(self):
        self.window.dismiss()
        self.assertFalse(self.window.isVisible())

        self.window.show_launcher()
        self.assertTrue(self.window.isVisible())


if __name__ == "__main__":
    unittest.main()
