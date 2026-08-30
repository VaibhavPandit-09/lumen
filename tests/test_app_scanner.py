"""
Unit tests for XDG .desktop application scanner and parser.
"""

import tempfile
import unittest
from pathlib import Path

from lumen.core.app_scanner import AppScanner
from lumen.core.runner import clean_desktop_exec


class TestAppScanner(unittest.TestCase):

    def test_clean_desktop_exec(self):
        self.assertEqual(clean_desktop_exec("firefox %u"), ["firefox"])
        self.assertEqual(clean_desktop_exec("/usr/bin/vlc --started-from-file %F"), ["/usr/bin/vlc", "--started-from-file"])
        self.assertEqual(clean_desktop_exec("code %F"), ["code"])

    def test_parse_desktop_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_file = Path(tmpdir) / "testapp.desktop"
            app_file.write_text("""[Desktop Entry]
Type=Application
Name=Test Application
GenericName=Text Editor
Comment=An awesome text editor
Exec=test-editor %f
Icon=accessories-text-editor
Categories=Utility;TextEditor;
Keywords=edit;code;text;
Actions=NewWindow;

[Desktop Action NewWindow]
Name=New Window
Exec=test-editor --new-window
Icon=window-new
""", encoding="utf-8")

            scanner = AppScanner()
            results = scanner.parse_desktop_file(app_file)

            self.assertEqual(len(results), 2)
            # Main app
            main_res = results[0]
            self.assertEqual(main_res.title, "Test Application")
            self.assertEqual(main_res.subtitle, "Text Editor")
            self.assertIn("edit", main_res.keywords)

            # Action
            action_res = results[1]
            self.assertEqual(action_res.title, "Test Application — New Window")
            self.assertEqual(action_res.badge, "Action")

    def test_hidden_application_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_file = Path(tmpdir) / "hiddenapp.desktop"
            app_file.write_text("""[Desktop Entry]
Type=Application
Name=Secret Application
Exec=secret-bin
""", encoding="utf-8")

            scanner = AppScanner(hidden_applications=["Secret Application"])
            results = scanner.parse_desktop_file(app_file)
            self.assertEqual(len(results), 0)

    def test_nodisplay_and_type_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nodisplay_file = Path(tmpdir) / "nodisp.desktop"
            nodisplay_file.write_text("""[Desktop Entry]
Type=Application
Name=Internal Tool
Exec=internal-tool
NoDisplay=true
""", encoding="utf-8")

            scanner = AppScanner()
            self.assertEqual(len(scanner.parse_desktop_file(nodisplay_file)), 0)


if __name__ == "__main__":
    unittest.main()
