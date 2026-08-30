"""
Unit tests for Custom Action discovery and caching.
"""

import tempfile
import unittest
from pathlib import Path

from lumen.core.actions.discovery import ActionScanner
from lumen.core.actions.manifest import ActionDefinition


class TestActionsDiscovery(unittest.TestCase):

    def test_discovery_and_caching(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            
            # Create a valid action manifest
            manifest = dir_path / "test_action.jsonc"
            manifest.write_text(
                """{
                    "id": "sample-act",
                    "name": "Sample Action",
                    "description": "Sample description",
                    "exec": ["echo", "hello"]
                }""",
                encoding="utf-8",
            )

            # Create an ignored hidden file
            hidden = dir_path / ".hidden_action.jsonc"
            hidden.write_text('{"id": "hidden", "name": "Hidden", "exec": ["echo"]}', encoding="utf-8")

            # Create an ignored non-json file
            non_json = dir_path / "notes.txt"
            non_json.write_text("random text", encoding="utf-8")

            scanner = ActionScanner(dir_path)
            actions = scanner.scan()

            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].id, "sample-act")
            self.assertEqual(actions[0].name, "Sample Action")

            # Second scan should hit cache
            cached_actions = scanner.scan()
            self.assertEqual(len(cached_actions), 1)
            self.assertEqual(cached_actions[0].id, "sample-act")


if __name__ == "__main__":
    unittest.main()
