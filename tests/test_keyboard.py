"""
Unit tests for keyboard interaction and search bar event handling.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from lumen.ui.search_bar import SearchBar


class TestKeyboardInteraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.search_bar = SearchBar()

    def tearDown(self):
        self.search_bar.close()

    def test_navigation_signals(self):
        nav_key = None

        def _on_nav(k):
            nonlocal nav_key
            nav_key = k

        self.search_bar.navigate_signal.connect(_on_nav)

        # Down arrow
        ev_down = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        self.search_bar.keyPressEvent(ev_down)
        self.assertEqual(nav_key, Qt.Key.Key_Down)

        # Up arrow
        ev_up = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        self.search_bar.keyPressEvent(ev_up)
        self.assertEqual(nav_key, Qt.Key.Key_Up)

    def test_activation_and_dismiss_signals(self):
        activated = False
        dismissed = False

        self.search_bar.activate_signal.connect(lambda: nonlocal_set_active())
        self.search_bar.dismiss_signal.connect(lambda: nonlocal_set_dismiss())

        def nonlocal_set_active():
            nonlocal activated
            activated = True

        def nonlocal_set_dismiss():
            nonlocal dismissed
            dismissed = True

        # Enter key
        ev_enter = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        self.search_bar.keyPressEvent(ev_enter)
        self.assertTrue(activated)

        # Escape key
        ev_esc = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        self.search_bar.keyPressEvent(ev_esc)
        self.assertTrue(dismissed)

    def test_drill_down_and_back_signals(self):
        drill_down = False
        pop_level = False

        self.search_bar.drill_down_signal.connect(lambda: nonlocal_set_drill())
        self.search_bar.pop_level_signal.connect(lambda: nonlocal_set_pop())

        def nonlocal_set_drill():
            nonlocal drill_down
            drill_down = True

        def nonlocal_set_pop():
            nonlocal pop_level
            pop_level = True

        # Tab key drills down
        ev_tab = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
        self.search_bar.keyPressEvent(ev_tab)
        self.assertTrue(drill_down)

        # Backspace on empty text pops level
        self.search_bar.clear()
        ev_bs = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        self.search_bar.keyPressEvent(ev_bs)
        self.assertTrue(pop_level)


if __name__ == "__main__":
    unittest.main()
