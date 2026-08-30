"""
Unit tests for configuration versioning, automatic backup creation, retention pruning, and migration.
"""

import tempfile
import time
import unittest
from pathlib import Path

from lumen.core.config import (
    CURRENT_CONFIG_VERSION,
    MAX_CONFIG_BACKUPS,
    ConfigMigrator,
    LumenConfig,
)


class TestConfigMigrations(unittest.TestCase):

    def test_backup_creation_and_pruning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.jsonc"
            config_path.write_text('{"shortcut": "Meta+Space"}', encoding="utf-8")

            # Create multiple backups
            backups = []
            for i in range(MAX_CONFIG_BACKUPS + 3):
                # Ensure unique timestamp
                time.sleep(0.01)
                b = ConfigMigrator.create_backup(config_path)
                self.assertIsNotNone(b)
                self.assertTrue(b.exists())
                backups.append(b)

            # Check retention limit
            existing_backups = list(config_path.parent.glob("config.jsonc.backup-*"))
            self.assertLessEqual(len(existing_backups), MAX_CONFIG_BACKUPS)

    def test_migration_from_unversioned_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            cfg_file = config_dir / "config.jsonc"
            # Write unversioned config (version 0 / none)
            cfg_file.write_text(
                '{"shortcut": "Super+Space", "theme": "dark"}',
                encoding="utf-8",
            )

            cfg = LumenConfig(config_dir=config_dir).load()

            # Should load existing user values
            self.assertEqual(cfg.shortcut, "Super+Space")
            self.assertEqual(cfg.theme, "dark")
            self.assertEqual(cfg.config_version, CURRENT_CONFIG_VERSION)

    def test_future_version_compatibility(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.jsonc"
            data = {"config_version": 999, "shortcut": "Alt+Space"}

            migrated, was_migrated = ConfigMigrator.migrate_if_needed(config_path, data)
            self.assertFalse(was_migrated)
            self.assertEqual(migrated["config_version"], 999)
            self.assertEqual(migrated["shortcut"], "Alt+Space")


if __name__ == "__main__":
    unittest.main()
