"""
Unit tests for installer and uninstaller execution in isolated temporary environments.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from lumen import __version__


class TestInstallerLifecycle(unittest.TestCase):

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.install_script = self.root_dir / "install.sh"
        self.uninstall_script = self.root_dir / "uninstall.sh"

    def test_install_check_mode(self):
        res = subprocess.run(
            ["bash", str(self.install_script), "--check"],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Preflight check successful", res.stdout)

    def test_install_version_mode(self):
        res = subprocess.run(
            ["bash", str(self.install_script), "--version"],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn(__version__, res.stdout)

    def test_uninstall_check_mode(self):
        res = subprocess.run(
            ["bash", str(self.uninstall_script), "--check"],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Uninstallation preview", res.stdout)

    def test_isolated_installation_and_uninstallation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_home = Path(tmpdir)
            env = os.environ.copy()
            env["HOME"] = str(temp_home)
            env["XDG_BIN_HOME"] = str(temp_home / ".local" / "bin")
            env["XDG_DATA_HOME"] = str(temp_home / ".local" / "share")
            env["XDG_CONFIG_HOME"] = str(temp_home / ".config")

            # 1. Run install in isolated home
            res_install = subprocess.run(
                ["bash", str(self.install_script)],
                cwd=str(self.root_dir),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_install.returncode, 0)

            # Verify installed files
            bin_file = temp_home / ".local" / "bin" / "lumen"
            desktop_file = temp_home / ".local" / "share" / "applications" / "lumen.desktop"
            icon_file = temp_home / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "lumen.svg"
            config_file = temp_home / ".config" / "lumen" / "config.jsonc"
            actions_dir = temp_home / ".config" / "lumen" / "actions"

            self.assertTrue(bin_file.exists())
            self.assertTrue(desktop_file.exists())
            self.assertTrue(icon_file.exists())
            self.assertTrue(config_file.exists())
            self.assertTrue(actions_dir.exists())

            # 2. Create custom user action to verify preservation
            custom_action = actions_dir / "user_custom.jsonc"
            custom_action.write_text('{"id": "user-custom", "name": "User Custom", "exec": ["echo"]}', encoding="utf-8")

            # 3. Run install again (upgrade simulation)
            res_upgrade = subprocess.run(
                ["bash", str(self.install_script)],
                cwd=str(self.root_dir),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_upgrade.returncode, 0)
            self.assertTrue(custom_action.exists())

            # 4. Run normal uninstaller
            res_uninstall = subprocess.run(
                ["bash", str(self.uninstall_script)],
                cwd=str(self.root_dir),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_uninstall.returncode, 0)

            # Application files should be removed
            self.assertFalse(bin_file.exists())
            self.assertFalse(desktop_file.exists())
            self.assertFalse(icon_file.exists())

            # User configuration and custom actions MUST be preserved
            self.assertTrue(config_file.exists())
            self.assertTrue(custom_action.exists())


if __name__ == "__main__":
    unittest.main()
