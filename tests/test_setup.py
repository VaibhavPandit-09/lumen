"""
Unit tests for KDE global shortcut management and first-run setup flow.
"""

import unittest
from unittest.mock import MagicMock, patch

from lumen.service.shortcuts import KDEShortcutManager


class TestKDEShortcutManager(unittest.TestCase):
    """Tests KDE Plasma global shortcut manager."""

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"})
    def test_is_kde_session_true(self):
        self.assertTrue(KDEShortcutManager.is_kde_session())

    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"})
    def test_is_kde_session_false(self):
        self.assertFalse(KDEShortcutManager.is_kde_session())

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_configure_shortcut_success(self, mock_run, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/" + cmd if cmd in ("kwriteconfig6", "qdbus6") else None
        mock_run.return_value = MagicMock(returncode=0)

        success, msg = KDEShortcutManager.configure_shortcut("Alt+Space")
        self.assertTrue(success)
        self.assertIn("configured successfully", msg)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_remove_shortcut_success(self, mock_run, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/" + cmd if cmd == "kwriteconfig6" else None
        mock_run.return_value = MagicMock(returncode=0)

        self.assertTrue(KDEShortcutManager.remove_shortcut())


if __name__ == "__main__":
    unittest.main()
