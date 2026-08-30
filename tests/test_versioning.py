"""
Unit tests for project version consistency and single-source-of-truth verification.
"""

import re
import unittest
from pathlib import Path

from lumen import __version__


class TestVersioning(unittest.TestCase):

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_pyproject_version_matches(self):
        pyproject_file = self.root_dir / "pyproject.toml"
        self.assertTrue(pyproject_file.is_file())
        text = pyproject_file.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), __version__)

    def test_pkgbuild_version_matches(self):
        pkgbuild_file = self.root_dir / "PKGBUILD"
        self.assertTrue(pkgbuild_file.is_file())
        text = pkgbuild_file.read_text(encoding="utf-8")
        match = re.search(r'pkgver\s*=\s*([0-9\.]+)', text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), __version__)

    def test_debian_changelog_version_matches(self):
        changelog_file = self.root_dir / "debian" / "changelog"
        self.assertTrue(changelog_file.is_file())
        first_line = changelog_file.read_text(encoding="utf-8").splitlines()[0]
        self.assertIn(f"({__version__}-1)", first_line)

    def test_semantic_version_format(self):
        # Must match semver (MAJOR.MINOR.PATCH)
        pattern = r"^\d+\.\d+\.\d+$"
        self.assertRegex(__version__, pattern)


if __name__ == "__main__":
    unittest.main()
