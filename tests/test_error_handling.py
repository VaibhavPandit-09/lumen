"""
Unit tests for error boundary isolation and failure recovery.
"""

import tempfile
import unittest
from pathlib import Path
from typing import List

from lumen.core.app_scanner import AppScanner
from lumen.core.models import SearchResult
from lumen.core.runner import launch_desktop_file, launch_shell_command
from lumen.providers.base import BaseProvider


class FaultyProvider(BaseProvider):
    """A provider that deliberately raises exceptions during search."""

    def __init__(self):
        super().__init__("faulty_provider", enabled=True)

    def search(self, query: str) -> List[SearchResult]:
        raise RuntimeError("Simulated internal provider crash")


class TestErrorHandling(unittest.TestCase):

    def test_faulty_provider_safe_search_isolation(self):
        prov = FaultyProvider()
        # safe_search should catch the RuntimeError and return []
        results = prov.safe_search("test")
        self.assertEqual(results, [])

    def test_corrupt_desktop_file_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            corrupt_file = Path(tmpdir) / "corrupt.desktop"
            corrupt_file.write_bytes(b"\x00\xff\xfe invalid binary garbage")

            scanner = AppScanner()
            results = scanner.parse_desktop_file(corrupt_file)
            self.assertEqual(results, [])

    def test_runner_missing_executable(self):
        # Should return False gracefully without raising unhandled exceptions
        self.assertFalse(launch_desktop_file("nonexistent_binary_xyz_12345"))


if __name__ == "__main__":
    unittest.main()
