"""
Optional KDE Plasma system tray companion icon for Lumen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from lumen import __version__
from lumen.core.logging import debug, info


class LumenTrayCompanion(QObject):
    """Manages the optional system tray icon and context menu."""

    def __init__(self, parent_window: Optional[QObject] = None):
        super().__init__(parent_window)
        self.window = parent_window
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._init_tray()

    def _get_app_icon(self) -> QIcon:
        """Finds application icon from assets or theme."""
        asset_icon_path = Path(__file__).resolve().parent.parent / "assets" / "lumen.svg"
        if asset_icon_path.is_file():
            icon = QIcon(str(asset_icon_path))
            if not icon.isNull():
                return icon
        return QIcon.fromTheme("lumen", QIcon.fromTheme("system-search"))

    def _init_tray(self) -> None:
        """Initializes the QSystemTrayIcon with actions and context menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            debug("Tray", "System tray is not available in current environment.")
            return

        icon = self._get_app_icon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip(f"Lumen — Command Launcher (v{__version__})")

        # Create context menu
        menu = QMenu()
        menu.setObjectName("LumenTrayMenu")

        # Toggle action
        toggle_action = QAction("Toggle Launcher", menu)
        toggle_action.triggered.connect(self._handle_toggle)
        menu.addAction(toggle_action)

        menu.addSeparator()

        # Reload action
        reload_action = QAction("Reload Configuration & Actions", menu)
        reload_action.triggered.connect(self._handle_reload)
        menu.addAction(reload_action)

        # About action
        about_action = QAction("About Lumen", menu)
        about_action.triggered.connect(self._handle_about)
        menu.addAction(about_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit Lumen", menu)
        quit_action.triggered.connect(self._handle_quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
        debug("Tray", "Lumen system tray icon initialized and shown.")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handles user clicking the system tray icon."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._handle_toggle()

    def _handle_toggle(self) -> None:
        if self.window and hasattr(self.window, "toggle"):
            self.window.toggle()

    def _handle_reload(self) -> None:
        if self.window and hasattr(self.window, "refresh_all_providers"):
            self.window.refresh_all_providers()
            info("Tray", "Reloaded configuration and custom actions.")

    def _handle_about(self) -> None:
        msg = (
            f"Lumen v{__version__}\n\n"
            "An agent-friendly command launcher for KDE Plasma.\n\n"
            "https://github.com/VaibhavPandit-09/lumen"
        )
        QMessageBox.about(None, "About Lumen", msg)

    def _handle_quit(self) -> None:
        app = QApplication.instance()
        if app:
            app.quit()

    def cleanup(self) -> None:
        """Hides and cleans up the tray icon before shutdown."""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
