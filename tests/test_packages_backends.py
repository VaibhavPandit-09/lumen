"""
Unit tests for package backends and PackageManager controller.
"""

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from lumen.core.packages.apt import AptBackend
from lumen.core.packages.base import PackageInfo, PackageOperationResult
from lumen.core.packages.flatpak import FlatpakBackend
from lumen.core.packages.manager import PackageManager
from lumen.core.packages.pacman import PacmanBackend
from lumen.core.packages.snap import SnapBackend


class TestPackageBackends(unittest.TestCase):
    """Tests package backend implementations with mocked subprocess commands."""

    @patch("shutil.which", return_value="/usr/bin/apt-cache")
    @patch("subprocess.run")
    def test_apt_search_and_installed(self, mock_run, mock_which):
        apt = AptBackend()
        self.assertTrue(apt.is_available())

        # Mock apt-cache search
        mock_res1 = MagicMock()
        mock_res1.returncode = 0
        mock_res1.stdout = "htop - interactive processes viewer\nbashtop - resource monitor\n"

        # Mock dpkg-query
        mock_res2 = MagicMock()
        mock_res2.returncode = 0
        mock_res2.stdout = "htop\t3.3.0\tinstall ok installed\n"

        mock_run.side_effect = [mock_res1, mock_res2]

        results = apt.search("htop")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "htop")
        self.assertTrue(results[0].installed)
        self.assertEqual(results[0].version, "3.3.0")
        self.assertFalse(results[1].installed)

    @patch("shutil.which", return_value="/usr/bin/flatpak")
    @patch("subprocess.run")
    def test_flatpak_search(self, mock_run, mock_which):
        fp = FlatpakBackend()
        self.assertTrue(fp.is_available())

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "org.mozilla.firefox\tFirefox\tWeb Browser\t130.0\n"
        mock_run.return_value = mock_res

        results = fp.search("firefox")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "org.mozilla.firefox")
        self.assertEqual(results[0].source_backend, "flatpak")
        self.assertTrue(results[0].is_gui_app)

    @patch("shutil.which", return_value="/usr/bin/snap")
    @patch("subprocess.run")
    def test_snap_search(self, mock_run, mock_which):
        snap = SnapBackend()
        self.assertTrue(snap.is_available())

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Name  Version  Rev  Tracking  Publisher  Notes  Summary\nvlc   3.0.18   123  latest    videolan   -      VLC Media Player\n"
        mock_run.return_value = mock_res

        results = snap.search("vlc")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "vlc")
        self.assertEqual(results[0].source_backend, "snap")

    @patch("shutil.which", return_value="/usr/bin/pacman")
    @patch("subprocess.run")
    def test_pacman_search(self, mock_run, mock_which):
        pac = PacmanBackend()
        self.assertTrue(pac.is_available())

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "extra/ripgrep 14.1.0-1 [installed]\n    A search tool that combines the usability of The Silver Searcher\n"
        mock_run.return_value = mock_res

        results = pac.search("ripgrep")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "ripgrep")
        self.assertTrue(results[0].installed)
        self.assertEqual(results[0].source_backend, "pacman")

    @patch.object(AptBackend, "is_locked", return_value=False)
    @patch("subprocess.run")
    def test_apt_install_success(self, mock_run, mock_locked):
        apt = AptBackend()
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Setting up tree (1.8.0)..."
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        res = apt.install("tree")
        self.assertTrue(res.success)
        self.assertIn("Successfully installed tree", res.message)

    def test_package_name_validation(self):
        apt = AptBackend()
        res = apt.install("tree; rm -rf /")
        self.assertFalse(res.success)
        self.assertIn("Invalid package name", res.message)

        flatpak = FlatpakBackend()
        res_fp = flatpak.install("org.app; rm -rf /")
        self.assertFalse(res_fp.success)
        self.assertIn("Invalid package name", res_fp.message)

        snap = SnapBackend()
        res_snap = snap.install("pkg $(whoami)")
        self.assertFalse(res_snap.success)
        self.assertIn("Invalid package name", res_snap.message)

        pacman = PacmanBackend()
        res_pac = pacman.install("pkg`id`")
        self.assertFalse(res_pac.success)
        self.assertIn("Invalid package name", res_pac.message)

    def test_backend_capabilities(self):
        apt = AptBackend()
        self.assertTrue(apt.capabilities["supports_purge"])
        self.assertTrue(apt.capabilities["supports_details"])

        flatpak = FlatpakBackend()
        self.assertTrue(flatpak.capabilities["supports_purge"])
        self.assertFalse(flatpak.capabilities["supports_details"])


class TestPackageManager(unittest.TestCase):
    """Tests aggregation and concurrency lock of PackageManager."""

    def test_manager_singleton(self):
        m1 = PackageManager.get_instance()
        m2 = PackageManager.get_instance()
        self.assertIs(m1, m2)

    def test_search_all_ranking(self):
        mock_backend = MagicMock()
        mock_backend.name = "MockAPT"
        mock_backend.is_available.return_value = True
        mock_backend.search.return_value = [
            PackageInfo(name="libtree", summary="tree library", installed=False),
            PackageInfo(name="tree", summary="directory viewer", installed=True),
        ]

        mgr = PackageManager()
        mgr.backends = {"mock": mock_backend}
        results = mgr.search_all("tree")
        self.assertEqual(len(results), 2)
        # Exact match and installed should rank first
        self.assertEqual(results[0].name, "tree")
        self.assertEqual(results[1].name, "libtree")


if __name__ == "__main__":
    unittest.main()
