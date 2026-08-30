"""
Unit tests for Phase 5 system doctor diagnostic checks.
"""

import unittest
from unittest.mock import MagicMock, patch

from lumen.core.doctor import CheckStatus, SystemDoctor


class TestDoctorPhase5(unittest.TestCase):
    """Tests new diagnostic checks added in Phase 5."""

    @patch("shutil.which")
    def test_privilege_escalation_detected(self, mock_which):
        mock_which.side_effect = lambda cmd: "/usr/bin/" + cmd if cmd == "pkexec" else None
        check = SystemDoctor.check_privilege_escalation()
        self.assertEqual(check.status, CheckStatus.PASS)
        self.assertIn("pkexec", check.message)

    @patch("shutil.which", return_value=None)
    def test_privilege_escalation_missing(self, mock_which):
        check = SystemDoctor.check_privilege_escalation()
        self.assertEqual(check.status, CheckStatus.WARN)
        self.assertIn("No privilege elevation tool", check.message)

    @patch("lumen.service.shortcuts.KDEShortcutManager.is_kde_session", return_value=True)
    @patch("lumen.service.shortcuts.KDEShortcutManager.get_active_shortcut", return_value="Alt+Space")
    def test_kde_shortcut_configured(self, mock_sc, mock_kde):
        check = SystemDoctor.check_global_shortcut()
        self.assertEqual(check.status, CheckStatus.PASS)
        self.assertIn("Alt+Space", check.message)

    @patch("lumen.service.shortcuts.KDEShortcutManager.is_kde_session", return_value=False)
    def test_non_kde_shortcut_info(self, mock_kde):
        check = SystemDoctor.check_global_shortcut()
        self.assertEqual(check.status, CheckStatus.INFO)


if __name__ == "__main__":
    unittest.main()
