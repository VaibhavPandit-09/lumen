"""
Unit tests for updater version comparison logic.
"""

from __future__ import annotations

import unittest

from lumen.core.updater.version import compare_versions


class TestVersionCompare(unittest.TestCase):
    """Unit tests for compare_versions."""

    def test_equal_versions(self) -> None:
        """Verify identical versions evaluate to 0."""
        self.assertEqual(compare_versions("0.5.0", "0.5.0"), 0)

    def test_patch_upgrade(self) -> None:
        """Verify patch upgrade returns 1."""
        self.assertEqual(compare_versions("0.5.1", "0.5.0"), 1)

    def test_minor_upgrade(self) -> None:
        """Verify minor upgrade returns 1."""
        self.assertEqual(compare_versions("0.6.0", "0.5.9"), 1)

    def test_major_upgrade(self) -> None:
        """Verify major upgrade returns 1."""
        self.assertEqual(compare_versions("1.0.0", "0.9.9"), 1)

    def test_downgrade(self) -> None:
        """Verify older version returns -1."""
        self.assertEqual(compare_versions("0.4.0", "0.5.0"), -1)

    def test_v_prefix_handling(self) -> None:
        """Verify leading 'v' and 'V' prefixes are stripped correctly."""
        self.assertEqual(compare_versions("v0.6.0", "0.5.0"), 1)
        self.assertEqual(compare_versions("0.5.0", "v0.5.0"), 0)
        self.assertEqual(compare_versions("V1.0.0", "v1.0.0"), 0)
        self.assertEqual(compare_versions("v0.4.0", "0.5.0"), -1)

    def test_unequal_length_versions(self) -> None:
        """Verify versions with different segment counts are padded properly."""
        self.assertEqual(compare_versions("1.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("1.0.1", "1.0"), 1)
        self.assertEqual(compare_versions("1.0", "1.0.1"), -1)
        self.assertEqual(compare_versions("2", "2.0.0.0"), 0)

    def test_non_numeric_graceful(self) -> None:
        """Verify non-numeric or malformed version strings are handled without crashing."""
        self.assertEqual(compare_versions("invalid", "0.0.0"), 0)
        self.assertEqual(compare_versions("1.0.0-beta", "1.0.0"), 0)
        self.assertEqual(compare_versions("1.0.0-rc1", "1.0.1"), -1)
        self.assertEqual(compare_versions("2.0.alpha", "1.9.9"), 1)
        self.assertEqual(compare_versions("", ""), 0)


if __name__ == "__main__":
    unittest.main()
