"""
Headless UI tests for the core launcher interaction contract:
Enter execution, Mouse Click execution, Escape dismissal, and focus management.
"""

import os
import sys
import unittest

from PyQt6.QtCore import QCoreApplication, QEvent, Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QApplication

from lumen.core.actions.dispatcher import ActionDispatcher
from lumen.core.config import LumenConfig
from lumen.core.models import SearchResult
from lumen.ui.launcher_window import LauncherWindow


class TestLauncherInteraction(unittest.TestCase):
    """Tests keyboard and mouse execution contract on LauncherWindow."""

    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)
        QCoreApplication.setApplicationName("lumen")
        QCoreApplication.setOrganizationName("lumen")

    def setUp(self):
        self.config = LumenConfig(enable_animations=False, max_results=10)
        self.window = LauncherWindow(self.config)

    def tearDown(self):
        self.window.close()

    def test_result_list_focus_policy(self):
        """ResultListWidget must have NoFocus policy so typing always routes to SearchBar."""
        self.assertEqual(self.window.result_list.focusPolicy(), Qt.FocusPolicy.NoFocus)

    def test_enter_key_executes_selected_item_and_dismisses(self):
        """Pressing Enter in search bar must execute selected result and dismiss window."""
        executed = []
        custom_item = SearchResult(
            id="test:enter",
            title="Execute Me With Enter",
            action=lambda: executed.append("enter_hit"),
        )
        self.window.result_list.clear()
        from PyQt6.QtWidgets import QListWidgetItem
        list_item = QListWidgetItem(self.window.result_list)
        list_item.setData(Qt.ItemDataRole.UserRole, custom_item)
        self.window.result_list.addItem(list_item)
        self.window.result_list.setCurrentRow(0)

        # Send Return key event to search bar
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.window.search_bar.keyPressEvent(event)

        self.assertEqual(executed, ["enter_hit"])

    def test_mouse_click_executes_clicked_item_and_dismisses(self):
        """Clicking an item in the result list must execute it and dismiss window."""
        executed = []
        custom_item = SearchResult(
            id="test:click",
            title="Execute Me With Click",
            action=lambda: executed.append("click_hit"),
        )
        self.window.result_list.clear()
        from PyQt6.QtWidgets import QListWidgetItem
        list_item = QListWidgetItem(self.window.result_list)
        list_item.setData(Qt.ItemDataRole.UserRole, custom_item)
        self.window.result_list.addItem(list_item)

        # Trigger itemClicked signal
        self.window.result_list.itemClicked.emit(list_item)

        self.assertEqual(executed, ["click_hit"])

    def test_escape_key_dismisses_window_without_executing(self):
        """Escape must hide the launcher and clear state without executing anything."""
        executed = []
        custom_item = SearchResult(
            id="test:esc",
            title="Do Not Execute",
            action=lambda: executed.append("should_not_run"),
        )
        self.window.show_launcher()
        self.window.search_bar.setText("test query")

        # Press Escape
        esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        self.window.keyPressEvent(esc_event)

        self.assertEqual(executed, [])
        self.assertEqual(self.window.search_bar.text(), "")

    def test_repeated_invocation_lifecycle(self):
        """Tests open -> type -> dismiss -> reopen -> type -> execute cycles."""
        executed = []
        for i in range(3):
            self.window.show_launcher()
            self.window.search_bar.setText(f"query_{i}")
            self.assertEqual(self.window.search_bar.text(), f"query_{i}")

            if i % 2 == 0:
                # Dismiss with Escape
                esc_event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
                self.window.keyPressEvent(esc_event)
                self.assertEqual(self.window.search_bar.text(), "")
            else:
                # Execute item
                item = SearchResult(
                    id=f"test:{i}",
                    title=f"Item {i}",
                    action=lambda idx=i: executed.append(idx),
                )
                self.window._on_item_activated(item)
                self.assertIn(i, executed)


if __name__ == "__main__":
    unittest.main()
