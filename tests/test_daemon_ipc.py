"""
Unit tests for single-instance IPC daemon and socket helpers.
"""

import os
import unittest
from pathlib import Path

from lumen.service.daemon import get_socket_path, is_daemon_running, send_ipc_command


class TestDaemonIPC(unittest.TestCase):

    def test_get_socket_path_format(self):
        socket_path = get_socket_path()
        self.assertIsInstance(socket_path, Path)
        self.assertTrue(str(socket_path).endswith("ipc.sock"))

    def test_is_daemon_running_when_no_server(self):
        # Should return False when no daemon is active
        self.assertFalse(is_daemon_running(timeout_ms=50))

    def test_send_ipc_command_fails_gracefully_when_no_daemon(self):
        # Should return False without throwing when no daemon is listening
        self.assertFalse(send_ipc_command("toggle", timeout_ms=50))


if __name__ == "__main__":
    unittest.main()
