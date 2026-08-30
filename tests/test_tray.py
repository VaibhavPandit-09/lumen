"""
Unit tests for optional KDE system tray companion.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QWidget
from lumen.ui.tray import LumenTrayCompanion


class TestTrayCompanion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.app.setApplicationName("lumen")
        cls.app.setOrganizationName("lumen")

    def test_tray_initialization_and_cleanup(self):
        parent = QWidget()
        tray = LumenTrayCompanion(parent)
        # Should initialize gracefully without crashing in offscreen mode
        tray.cleanup()
        self.assertIsNone(tray.tray_icon)


if __name__ == "__main__":
    unittest.main()
