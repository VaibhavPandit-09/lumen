"""
Single-instance daemon and IPC server for instant launcher activation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication

from lumen.core.config import LumenConfig
from lumen.ui.launcher_window import LauncherWindow


def get_socket_name() -> str:
    """Returns unique user-specific local socket name."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    uid = os.getuid() if hasattr(os, "getuid") else 1000
    return str(Path(runtime_dir) / f"lumen_ipc_{uid}.sock")


def send_ipc_command(command: str, timeout_ms: int = 400) -> bool:
    """
    Attempts to send a command to an existing running Lumen daemon instance.
    Returns True if successfully delivered, False if no daemon is listening.
    """
    socket = QLocalSocket()
    socket_name = get_socket_name()
    socket.connectToServer(socket_name)

    if socket.waitForConnected(timeout_ms):
        msg = (command.strip() + "\n").encode("utf-8")
        socket.write(msg)
        socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        return True

    return False


class LumenAppDaemon(QObject):
    """Manages single-instance lifecycle and receives IPC commands from global shortcuts or CLI."""

    def __init__(self, config: Optional[LumenConfig] = None):
        super().__init__()
        self.config = config or LumenConfig().load()
        self.window: Optional[LauncherWindow] = None
        self.server: Optional[QLocalServer] = None

    def start(self, show_immediately: bool = True) -> int:
        """Starts the local server and runs the application event loop."""
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        app.setApplicationName("Lumen")
        app.setOrganizationName("Lumen")
        app.setQuitOnLastWindowClosed(False)

        # Setup local IPC server
        socket_name = get_socket_name()
        # Clean up stale socket file if any
        if os.path.exists(socket_name):
            try:
                os.remove(socket_name)
            except OSError:
                pass

        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_incoming_connection)
        if not self.server.listen(socket_name):
            print(f"[Lumen Daemon] Warning: Could not listen on socket {socket_name}")

        # Initialize launcher window
        self.window = LauncherWindow(config=self.config)

        if show_immediately:
            self.window.show_launcher()

        return app.exec()

    def _handle_incoming_connection(self) -> None:
        """Handles commands received from client instances (e.g. `lumen toggle`)."""
        if not self.server:
            return

        client_socket = self.server.nextPendingConnection()
        if not client_socket:
            return

        if client_socket.waitForReadyRead(200):
            raw_data = bytes(client_socket.readAll()).decode("utf-8").strip()
            self._process_command(raw_data)

        client_socket.disconnectFromServer()

    def _process_command(self, cmd: str) -> None:
        """Processes IPC command strings."""
        if not self.window:
            return

        c = cmd.lower()
        if c in ("toggle", ""):
            self.window.toggle()
        elif c == "show":
            self.window.show_launcher()
        elif c == "hide":
            self.window.dismiss()
        elif c == "refresh":
            self.window.config.load()
            self.window.refresh_all_providers()
        elif c == "quit":
            app = QApplication.instance()
            if app:
                app.quit()
