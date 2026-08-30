"""
Single-instance daemon and IPC server for instant launcher activation.
"""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication

from lumen.core.config import LumenConfig
from lumen.core.logging import debug, error, info, warning
from lumen.ui.launcher_window import LauncherWindow


def get_socket_path() -> Path:
    """Returns unique, securely-permissioned user-specific local socket path."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    uid = os.getuid() if hasattr(os, "getuid") else 1000

    if runtime_dir and os.path.isdir(runtime_dir):
        base_dir = Path(runtime_dir) / "lumen"
    else:
        base_dir = Path(f"/tmp/lumen_{uid}")

    try:
        base_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    except Exception:
        pass

    return base_dir / "ipc.sock"


def is_daemon_running(timeout_ms: int = 150) -> bool:
    """Probes whether another Lumen daemon is actively listening on the IPC socket."""
    socket_path = get_socket_path()
    if not socket_path.exists():
        return False

    socket = QLocalSocket()
    socket.connectToServer(str(socket_path))
    connected = socket.waitForConnected(timeout_ms)
    if connected:
        socket.disconnectFromServer()
        return True
    return False


def send_ipc_command(command: str, timeout_ms: int = 400) -> bool:
    """
    Attempts to send a command to an existing running Lumen daemon instance.
    Returns True if successfully delivered, False if no daemon is listening.
    """
    socket_path = get_socket_path()
    if not socket_path.exists():
        return False

    socket = QLocalSocket()
    socket.connectToServer(str(socket_path))

    if socket.waitForConnected(timeout_ms):
        msg = (command.strip() + "\n").encode("utf-8")
        socket.write(msg)
        socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        debug("IPC", f"Sent command '{command.strip()}' to daemon.")
        return True

    return False


class LumenAppDaemon(QObject):
    """Manages single-instance lifecycle and receives IPC commands from global shortcuts or CLI."""

    def __init__(self, config: Optional[LumenConfig] = None):
        super().__init__()
        self.config = config or LumenConfig().load()
        self.window: Optional[LauncherWindow] = None
        self.server: Optional[QLocalServer] = None
        self.socket_path = get_socket_path()

    def start(self, show_immediately: bool = True) -> int:
        """Starts the local server and runs the application event loop."""
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        app.setApplicationName("Lumen")
        app.setOrganizationName("Lumen")
        app.setQuitOnLastWindowClosed(False)

        # Probe for existing active daemon
        if is_daemon_running():
            debug("IPC", "Another daemon is already active. Forwarding show request.")
            send_ipc_command("show" if show_immediately else "refresh")
            return 0

        # Remove stale socket file if it exists from previous crash
        if self.socket_path.exists():
            try:
                self.socket_path.unlink(missing_ok=True)
                debug("IPC", f"Removed stale socket {self.socket_path}")
            except OSError as e:
                warning("IPC", f"Could not remove stale socket: {e}")

        # Setup local IPC server
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_incoming_connection)
        if not self.server.listen(str(self.socket_path)):
            error("IPC", f"Could not listen on socket {self.socket_path}")
        else:
            debug("IPC", f"Listening on IPC socket: {self.socket_path}")

        # Register signal handlers for clean exit
        self._setup_signal_handlers()

        # Initialize launcher window
        self.window = LauncherWindow(config=self.config)

        if show_immediately:
            self.window.show_launcher()

        ret = app.exec()
        self._cleanup_socket()
        return ret

    def _setup_signal_handlers(self) -> None:
        """Registers OS signal handlers for graceful socket cleanup."""
        def _sig_handler(sig, frame):
            info("IPC", f"Received signal {sig}. Exiting gracefully...")
            self._cleanup_socket()
            app = QApplication.instance()
            if app:
                app.quit()

        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)

    def _cleanup_socket(self) -> None:
        """Removes the IPC socket file."""
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
        if self.socket_path.exists():
            try:
                self.socket_path.unlink(missing_ok=True)
                debug("IPC", "Cleaned up IPC socket.")
            except Exception:
                pass

    def _handle_incoming_connection(self) -> None:
        """Handles commands received from client instances (e.g. `lumen toggle`)."""
        if not self.server:
            return

        client_socket = self.server.nextPendingConnection()
        if not client_socket:
            return

        if client_socket.waitForReadyRead(200):
            raw_data = bytes(client_socket.readAll()).decode("utf-8").strip()
            debug("IPC", f"Received command from socket: '{raw_data}'")
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
