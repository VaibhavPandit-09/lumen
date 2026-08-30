"""
Unit tests for configuration manager, JSONC parsing, and models.
"""

import json
import tempfile
import unittest
from pathlib import Path

from lumen.core.config import LumenConfig, parse_jsonc, strip_jsonc_comments
from lumen.core.models import CommandItem


class TestConfig(unittest.TestCase):

    def test_strip_jsonc_comments(self):
        jsonc = """
        // Single line comment
        {
          /* Multi line
             comment */
          "name": "Lumen",
          "shortcut": "Meta+Space", // inline comment
          "count": 42,
        }
        """
        data = parse_jsonc(jsonc)
        self.assertEqual(data["name"], "Lumen")
        self.assertEqual(data["shortcut"], "Meta+Space")
        self.assertEqual(data["count"], 42)

    def test_command_item_serialization(self):
        cmd = CommandItem(
            name="Restart Docker",
            command="docker compose restart",
            description="Restart dev containers",
            category="Development",
            terminal=True,
            subcommands=[
                CommandItem(name="Child", command="echo child"),
            ],
        )
        d = cmd.to_dict()
        self.assertEqual(d["name"], "Restart Docker")
        self.assertEqual(d["command"], "docker compose restart")
        self.assertTrue(d["terminal"])
        self.assertEqual(len(d["subcommands"]), 1)

        reconstructed = CommandItem.from_dict(d)
        self.assertEqual(reconstructed.name, "Restart Docker")
        self.assertEqual(len(reconstructed.subcommands), 1)
        self.assertEqual(reconstructed.subcommands[0].name, "Child")

    def test_lumen_config_load_and_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            cfg = LumenConfig(config_dir=config_dir)
            cfg.load()

            self.assertTrue(cfg.config_file.exists())
            self.assertTrue(cfg.commands_file.exists())
            self.assertEqual(cfg.shortcut, "Alt+Space")
            self.assertGreater(len(cfg.commands), 0)

            # Add a new command
            new_cmd = CommandItem(name="Test Command", command="echo test")
            cfg.add_command(new_cmd)

            # Reload
            cfg2 = LumenConfig(config_dir=config_dir).load()
            names = [c.name for c in cfg2.commands]
            self.assertIn("Test Command", names)


if __name__ == "__main__":
    unittest.main()
