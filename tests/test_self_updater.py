"""
Unit tests for the self-updater installer module and atomic update/rollback flow.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lumen.core.updater.checker import UpdateInfo
from lumen.core.updater.installer import InstallMethod, SelfUpdater, UpdateResult


class TestSelfUpdater(unittest.TestCase):
    """Unit tests for SelfUpdater and UpdateResult."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_home = Path(self.temp_dir.name)

        # Setup mock local installation structure
        self.mock_bin_dir = self.mock_home / ".local" / "bin"
        self.mock_bin_dir.mkdir(parents=True, exist_ok=True)
        self.mock_wrapper = self.mock_bin_dir / "lumen"

        self.mock_install_dir = self.mock_home / ".local" / "share" / "lumen"
        self.mock_install_dir.mkdir(parents=True, exist_ok=True)
        self.mock_app_dir = self.mock_install_dir / "lumen"
        self.mock_app_dir.mkdir(parents=True, exist_ok=True)
        (self.mock_app_dir / "__init__.py").write_text('__version__ = "0.5.0"\n', encoding="utf-8")
        (self.mock_install_dir / "original_canary.txt").write_text("v0.5.0 canary", encoding="utf-8")

        self.mock_wrapper.write_text(
            f'#!/bin/sh\ncd "{self.mock_install_dir}"\npython3 -m lumen\n',
            encoding="utf-8",
        )

        self.updater = SelfUpdater()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_tarball(self, files: dict[str, str]) -> tuple[bytes, str]:
        """Creates an in-memory tar.gz and returns (bytes, sha256_hex)."""
        bio = io.BytesIO()
        with tarfile.open(fileobj=bio, mode="w:gz") as tar:
            for arcname, content in files.items():
                data = content.encode("utf-8")
                ti = tarfile.TarInfo(name=arcname)
                ti.size = len(data)
                ti.mtime = 0
                tar.addfile(ti, io.BytesIO(data))
        tar_bytes = bio.getvalue()
        sha256 = hashlib.sha256(tar_bytes).hexdigest()
        return tar_bytes, sha256

    def test_detect_install_method_dev(self) -> None:
        """Mock git repo detection -> DEVELOPMENT."""
        def fake_exists(*args: tuple, **kwargs: dict) -> bool:
            return True

        with patch.object(Path, "exists", side_effect=fake_exists):
            method = SelfUpdater.detect_install_method()
            self.assertEqual(method, InstallMethod.DEVELOPMENT)

    def test_can_self_update(self) -> None:
        """USER_LOCAL -> True, others -> False."""
        self.assertTrue(SelfUpdater.can_self_update(InstallMethod.USER_LOCAL))
        self.assertFalse(SelfUpdater.can_self_update(InstallMethod.DEVELOPMENT))
        self.assertFalse(SelfUpdater.can_self_update(InstallMethod.DEBIAN))
        self.assertFalse(SelfUpdater.can_self_update(InstallMethod.ARCH))
        self.assertFalse(SelfUpdater.can_self_update(InstallMethod.PIP))
        self.assertFalse(SelfUpdater.can_self_update(InstallMethod.UNKNOWN))

    def test_update_rejects_non_user_local(self) -> None:
        """When method is DEBIAN, verify update returns success=False with informative message."""
        update_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            download_url="https://github.com/example/lumen.tar.gz",
        )
        with patch.object(SelfUpdater, "detect_install_method", return_value=InstallMethod.DEBIAN):
            result = self.updater.update(update_info)
            self.assertFalse(result.success)
            self.assertIn("Cannot self-update", result.message)
            self.assertIn("debian", result.message)
            self.assertFalse(result.rollback_performed)

    def test_update_checksum_verification_failure(self) -> None:
        """Create mock staging tarball with mismatching SHA256SUMS, verify update aborts."""
        tar_bytes, _ = self._create_tarball({
            "lumen/__init__.py": '__version__ = "0.6.0"\n',
        })
        mismatched_sha = "0000000000000000000000000000000000000000000000000000000000000000"

        update_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            download_url="https://github.com/example/lumen.tar.gz",
            checksum_url="https://github.com/example/SHA256SUMS",
        )

        def mock_retrieve(url: str, filename: str) -> None:
            if "SHA256SUMS" in url or "SHA256SUMS" in str(filename):
                Path(filename).write_text(f"{mismatched_sha}  update.tar.gz\n", encoding="utf-8")
            else:
                Path(filename).write_bytes(tar_bytes)

        with patch.object(SelfUpdater, "detect_install_method", return_value=InstallMethod.USER_LOCAL), \
             patch("pathlib.Path.home", return_value=self.mock_home), \
             patch("urllib.request.urlretrieve", side_effect=mock_retrieve):

            result = self.updater.update(update_info)
            self.assertFalse(result.success)
            self.assertEqual(result.message, "Checksum verification failed.")
            self.assertFalse(result.rollback_performed)

    def test_update_staging_and_extraction(self) -> None:
        """Mock download, verify tarball extraction and structure validation."""
        # 1. Valid package structure
        tar_bytes, real_sha = self._create_tarball({
            "lumen/__init__.py": '__version__ = "0.6.0"\n',
            "lumen/new_feature.py": '# New feature code\n',
        })

        update_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            download_url="https://github.com/example/lumen.tar.gz",
            checksum_url="https://github.com/example/SHA256SUMS",
        )

        def mock_retrieve(url: str, filename: str) -> None:
            if "SHA256SUMS" in url or "SHA256SUMS" in str(filename):
                Path(filename).write_text(f"{real_sha}  update.tar.gz\n", encoding="utf-8")
            else:
                Path(filename).write_bytes(tar_bytes)

        mock_subprocess_result = MagicMock()
        mock_subprocess_result.returncode = 0
        mock_subprocess_result.stdout = "0.6.0\n"
        mock_subprocess_result.stderr = ""

        progress_messages: list[str] = []

        with patch.object(SelfUpdater, "detect_install_method", return_value=InstallMethod.USER_LOCAL), \
             patch("pathlib.Path.home", return_value=self.mock_home), \
             patch("urllib.request.urlretrieve", side_effect=mock_retrieve), \
             patch("subprocess.run", return_value=mock_subprocess_result):

            result = self.updater.update(update_info, on_progress=progress_messages.append)
            self.assertTrue(result.success)
            self.assertEqual(result.new_version, "0.6.0")
            self.assertEqual(result.message, "Update successful")
            self.assertFalse(result.rollback_performed)
            self.assertTrue(len(progress_messages) > 0)
            self.assertIn("Downloading source tarball...", progress_messages)
            self.assertIn("Extracting files...", progress_messages)

        # 2. Invalid package structure (no lumen/__init__.py)
        invalid_tar_bytes, invalid_sha = self._create_tarball({
            "other_folder/readme.txt": "wrong package structure",
        })

        def mock_retrieve_invalid(url: str, filename: str) -> None:
            if "SHA256SUMS" in url or "SHA256SUMS" in str(filename):
                Path(filename).write_text(f"{invalid_sha}  update.tar.gz\n", encoding="utf-8")
            else:
                Path(filename).write_bytes(invalid_tar_bytes)

        with patch.object(SelfUpdater, "detect_install_method", return_value=InstallMethod.USER_LOCAL), \
             patch("pathlib.Path.home", return_value=self.mock_home), \
             patch("urllib.request.urlretrieve", side_effect=mock_retrieve_invalid):

            result = self.updater.update(update_info)
            self.assertFalse(result.success)
            self.assertEqual(result.message, "Invalid update package structure.")

    def test_update_atomic_rollback_on_verify_failure(self) -> None:
        """Mock verification command failure (exit code 1), verify target directory is restored from backup."""
        tar_bytes, real_sha = self._create_tarball({
            "lumen/__init__.py": '__version__ = "0.6.0"\n',
            "lumen/corrupted.py": 'broken syntax',
        })

        update_info = UpdateInfo(
            current_version="0.5.0",
            latest_version="0.6.0",
            update_available=True,
            download_url="https://github.com/example/lumen.tar.gz",
            checksum_url="https://github.com/example/SHA256SUMS",
        )

        def mock_retrieve(url: str, filename: str) -> None:
            if "SHA256SUMS" in url or "SHA256SUMS" in str(filename):
                Path(filename).write_text(f"{real_sha}  update.tar.gz\n", encoding="utf-8")
            else:
                Path(filename).write_bytes(tar_bytes)

        mock_subprocess_fail = MagicMock()
        mock_subprocess_fail.returncode = 1
        mock_subprocess_fail.stdout = ""
        mock_subprocess_fail.stderr = "Verification syntax error in lumen"

        with patch.object(SelfUpdater, "detect_install_method", return_value=InstallMethod.USER_LOCAL), \
             patch("pathlib.Path.home", return_value=self.mock_home), \
             patch("urllib.request.urlretrieve", side_effect=mock_retrieve), \
             patch("subprocess.run", return_value=mock_subprocess_fail):

            result = self.updater.update(update_info)
            self.assertFalse(result.success)
            self.assertTrue(result.rollback_performed)
            self.assertIn("Verification failed", result.message)

            # Check that the original directory was restored
            self.assertTrue(self.mock_install_dir.exists())
            self.assertTrue((self.mock_install_dir / "original_canary.txt").exists())
            self.assertEqual(
                (self.mock_install_dir / "original_canary.txt").read_text(encoding="utf-8"),
                "v0.5.0 canary",
            )
            # Check that temporary backup dir was removed / renamed back
            backup_dir = self.mock_install_dir.with_suffix(".backup")
            self.assertFalse(backup_dir.exists())


if __name__ == "__main__":
    unittest.main()
