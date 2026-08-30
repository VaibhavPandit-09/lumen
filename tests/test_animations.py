"""
Unit tests for WindowAnimationManager.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QWidget
from lumen.ui.animations import WindowAnimationManager


class TestAnimations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.widget = QWidget()
        self.anim_mgr = WindowAnimationManager(self.widget, duration_ms=50)

    def tearDown(self):
        self.widget.close()

    def test_zero_duration_animation_calls_callback(self):
        zero_mgr = WindowAnimationManager(self.widget, duration_ms=0)
        called = False

        def _on_finish():
            nonlocal called
            called = True

        zero_mgr.animate_show(on_finished=_on_finish)
        self.assertTrue(called)
        self.assertTrue(self.widget.isVisible())

        called_hide = False

        def _on_hide():
            nonlocal called_hide
            called_hide = True

        zero_mgr.animate_hide(on_finished=_on_hide)
        self.assertTrue(called_hide)
        self.assertFalse(self.widget.isVisible())

    def test_property_animation_instantiation(self):
        self.anim_mgr.animate_show()
        self.assertIsNotNone(self.anim_mgr._current_anim)


if __name__ == "__main__":
    unittest.main()
