"""
System health and diagnostic subsystem for Lumen.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from lumen import __version__
from lumen.core.actions.discovery import ActionScanner
from lumen.core.actions.validator import ActionValidator, IssueSeverity
from lumen.core.config import LumenConfig, parse_jsonc
from lumen.service.daemon import get_socket_path, is_daemon_running


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    INFO = "INFO"


@dataclass
class DiagnosticCheck:
    name: str
    status: CheckStatus
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": str(self.details) if self.details is not None else None,
            "fix_suggestion": str(self.fix_suggestion) if self.fix_suggestion is not None else None,
        }


@dataclass
class DoctorReport:
    version: str = __version__
    checks: List[DiagnosticCheck] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return not any(c.status == CheckStatus.FAIL for c in self.checks)

    @property
    def has_warnings(self) -> bool:
        return any(c.status == CheckStatus.WARN for c in self.checks)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "healthy": self.is_healthy,
            "has_warnings": self.has_warnings,
            "checks": [c.to_dict() for c in self.checks],
        }

    def format_text(self) -> str:
        lines = [
            f"=== Lumen Doctor Diagnostic Report (v{self.version}) ===",
            "",
        ]
        icons = {
            CheckStatus.PASS: "✓",
            CheckStatus.WARN: "⚠️",
            CheckStatus.FAIL: "❌",
            CheckStatus.INFO: "ℹ️",
        }
        for c in self.checks:
            icon = icons.get(c.status, "•")
            lines.append(f"{icon} [{c.status.value}] {c.name}: {c.message}")
            if c.details:
                lines.append(f"    Details: {c.details}")
            if c.fix_suggestion:
                lines.append(f"    Fix: {c.fix_suggestion}")
        lines.append("")
        if self.is_healthy and not self.has_warnings:
            lines.append("✓ All diagnostic checks passed. Lumen system health is excellent.")
        elif self.is_healthy:
            lines.append("⚠️ System is functional with minor warnings.")
        else:
            lines.append("❌ Action required: One or more critical checks failed.")
        lines.append("==================================================")
        return "\n".join(lines)


class SystemDoctor:
    """Executes full diagnostic suite across environment, dependencies, and integration."""

    @classmethod
    def run_all_checks(cls, config: Optional[LumenConfig] = None) -> DoctorReport:
        cfg = config or LumenConfig().load()
        report = DoctorReport()

        report.checks.append(cls.check_python_version())
        report.checks.append(cls.check_pyqt6())
        report.checks.append(cls.check_desktop_session())
        report.checks.append(cls.check_path_environment())
        report.checks.append(cls.check_executable_wrapper())
        report.checks.append(cls.check_desktop_entry())
        report.checks.append(cls.check_icon_asset())
        report.checks.append(cls.check_configuration(cfg))
        report.checks.append(cls.check_custom_actions(cfg))
        report.checks.append(cls.check_package_backends())
        report.checks.append(cls.check_privilege_escalation())
        report.checks.append(cls.check_global_shortcut())
        report.checks.append(cls.check_ipc_daemon())
        report.checks.append(cls.check_krunner_interface())
        report.checks.append(cls.check_system_tray())

        return report

    @staticmethod
    def check_python_version() -> DiagnosticCheck:
        py_ver = sys.version_info
        v_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
        if py_ver.major >= 3 and py_ver.minor >= 10:
            return DiagnosticCheck(
                name="Python Runtime",
                status=CheckStatus.PASS,
                message=f"Python {v_str} meets requirements (>= 3.10)",
            )
        return DiagnosticCheck(
            name="Python Runtime",
            status=CheckStatus.FAIL,
            message=f"Python {v_str} is unsupported (requires >= 3.10)",
            fix_suggestion="Upgrade your Python runtime to 3.10 or newer.",
        )

    @staticmethod
    def check_pyqt6() -> DiagnosticCheck:
        try:
            import PyQt6.QtCore  # noqa: F401
            import PyQt6.QtWidgets  # noqa: F401
            from PyQt6.QtCore import PYQT_VERSION_STR
            return DiagnosticCheck(
                name="PyQt6 Bindings",
                status=CheckStatus.PASS,
                message=f"PyQt6 {PYQT_VERSION_STR} is available",
            )
        except ImportError as e:
            return DiagnosticCheck(
                name="PyQt6 Bindings",
                status=CheckStatus.FAIL,
                message="PyQt6 is not installed or importable",
                details=str(e),
                fix_suggestion="Install PyQt6 via your package manager (e.g., 'sudo apt install python3-pyqt6' or 'pip install PyQt6')",
            )

    @staticmethod
    def check_desktop_session() -> DiagnosticCheck:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")
        session_type = os.environ.get("XDG_SESSION_TYPE", "Unknown")
        is_kde = "kde" in desktop.lower() or "plasma" in desktop.lower()

        if is_kde:
            return DiagnosticCheck(
                name="Desktop Session",
                status=CheckStatus.PASS,
                message=f"KDE Plasma detected ({session_type} session)",
                details=f"XDG_CURRENT_DESKTOP={desktop}",
            )
        return DiagnosticCheck(
            name="Desktop Session",
            status=CheckStatus.INFO,
            message=f"Non-KDE desktop session detected ({desktop}, {session_type})",
            details="Lumen is optimized for KDE Plasma but functions on any FreeDesktop-compliant desktop environment.",
        )

    @staticmethod
    def check_path_environment() -> DiagnosticCheck:
        home_bin = os.path.expanduser("~/.local/bin")
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)

        if home_bin in path_dirs:
            return DiagnosticCheck(
                name="PATH Environment",
                status=CheckStatus.PASS,
                message="~/.local/bin is present in PATH",
            )

        # Detect user shell
        shell = Path(os.environ.get("SHELL", "/bin/bash")).name
        if shell == "zsh":
            rc_cmd = "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc && source ~/.zshrc"
        elif shell == "fish":
            rc_cmd = "fish_add_path ~/.local/bin"
        else:
            rc_cmd = "echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc && source ~/.bashrc"

        return DiagnosticCheck(
            name="PATH Environment",
            status=CheckStatus.WARN,
            message="~/.local/bin is not in your current PATH",
            details="CLI commands such as 'lumen' may not be found directly without specifying the full path.",
            fix_suggestion=f"Add ~/.local/bin to your PATH: {rc_cmd}",
        )

    @staticmethod
    def check_executable_wrapper() -> DiagnosticCheck:
        target_path = Path(os.path.expanduser("~/.local/bin/lumen"))
        which_path = shutil.which("lumen")

        if which_path and os.path.isabs(which_path):
            return DiagnosticCheck(
                name="Lumen Executable",
                status=CheckStatus.PASS,
                message=f"Found executable at {which_path}",
            )
        if target_path.exists() and os.access(target_path, os.X_OK):
            return DiagnosticCheck(
                name="Lumen Executable",
                status=CheckStatus.PASS,
                message=f"Installed at {target_path} (executable)",
            )
        return DiagnosticCheck(
            name="Lumen Executable",
            status=CheckStatus.WARN,
            message="Lumen executable wrapper not found in ~/.local/bin/lumen",
            fix_suggestion="Run './install.sh' to install user-local wrapper.",
        )

    @staticmethod
    def check_desktop_entry() -> DiagnosticCheck:
        user_desktop = Path(os.path.expanduser("~/.local/share/applications/lumen.desktop"))
        sys_desktop = Path("/usr/share/applications/lumen.desktop")

        if user_desktop.exists():
            return DiagnosticCheck(
                name="Desktop Entry",
                status=CheckStatus.PASS,
                message=f"Desktop entry found at {user_desktop}",
            )
        if sys_desktop.exists():
            return DiagnosticCheck(
                name="Desktop Entry",
                status=CheckStatus.PASS,
                message=f"System desktop entry found at {sys_desktop}",
            )
        return DiagnosticCheck(
            name="Desktop Entry",
            status=CheckStatus.WARN,
            message="Desktop entry lumen.desktop not found",
            fix_suggestion="Run './install.sh' to register the application launcher.",
        )

    @staticmethod
    def check_icon_asset() -> DiagnosticCheck:
        user_icon = Path(os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps/lumen.svg"))
        sys_icon = Path("/usr/share/icons/hicolor/scalable/apps/lumen.svg")

        if user_icon.exists():
            return DiagnosticCheck(
                name="Icon Asset",
                status=CheckStatus.PASS,
                message=f"SVG icon installed at {user_icon}",
            )
        if sys_icon.exists():
            return DiagnosticCheck(
                name="Icon Asset",
                status=CheckStatus.PASS,
                message=f"System SVG icon installed at {sys_icon}",
            )
        return DiagnosticCheck(
            name="Icon Asset",
            status=CheckStatus.WARN,
            message="Scalable SVG icon not found in standard icon directories",
            fix_suggestion="Run './install.sh' to install icon assets.",
        )

    @staticmethod
    def check_configuration(config: LumenConfig) -> DiagnosticCheck:
        cfg_file = config.config_file
        if not cfg_file.exists():
            return DiagnosticCheck(
                name="Configuration Files",
                status=CheckStatus.INFO,
                message="Config file not yet created on disk (using built-in defaults)",
                details=str(cfg_file),
            )
        try:
            text = cfg_file.read_text(encoding="utf-8")
            data = parse_jsonc(text)
            ver = data.get("config_version", 1)
            return DiagnosticCheck(
                name="Configuration Files",
                status=CheckStatus.PASS,
                message=f"Configuration valid (config_version: {ver})",
                details=str(cfg_file),
            )
        except Exception as e:
            return DiagnosticCheck(
                name="Configuration Files",
                status=CheckStatus.FAIL,
                message="Configuration file has syntax errors",
                details=f"{cfg_file}: {e}",
                fix_suggestion=f"Fix JSON syntax in {cfg_file} or restore from a backup.",
            )

    @staticmethod
    def check_custom_actions(config: LumenConfig) -> DiagnosticCheck:
        scanner = ActionScanner(config.actions_dir)
        actions = scanner.scan()
        issues = ActionValidator.validate_action_collection(actions)
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]

        if errors:
            return DiagnosticCheck(
                name="Custom Actions",
                status=CheckStatus.WARN,
                message=f"{len(actions)} actions found, but {len(errors)} validation errors detected",
                details=f"Errors: {', '.join(e.message for e in errors[:3])}",
                fix_suggestion="Run 'lumen actions validate' for diagnostic details.",
            )
        return DiagnosticCheck(
            name="Custom Actions",
            status=CheckStatus.PASS,
            message=f"{len(actions)} custom action manifests validated successfully",
            details=str(scanner.get_actions_dir()),
        )

    @staticmethod
    def check_ipc_daemon() -> DiagnosticCheck:
        socket_path = get_socket_path()
        running = is_daemon_running()
        if running:
            return DiagnosticCheck(
                name="Daemon & IPC Socket",
                status=CheckStatus.PASS,
                message="Single-instance daemon is active and responding",
                details=socket_path,
            )
        return DiagnosticCheck(
            name="Daemon & IPC Socket",
            status=CheckStatus.INFO,
            message="No daemon running (launches on-demand)",
            details=socket_path,
        )

    @staticmethod
    def check_krunner_interface() -> DiagnosticCheck:
        # Check if D-Bus is present
        if shutil.which("qdbus6") or shutil.which("qdbus") or shutil.which("dbus-send"):
            return DiagnosticCheck(
                name="KRunner Interoperability",
                status=CheckStatus.PASS,
                message="D-Bus tools available for optional KRunner runner queries",
            )
        return DiagnosticCheck(
            name="KRunner Interoperability",
            status=CheckStatus.INFO,
            message="D-Bus query tools not found (KRunner provider operates in graceful fallback)",
        )

    @staticmethod
    def check_package_backends() -> DiagnosticCheck:
        from lumen.core.packages.manager import PackageManager
        mgr = PackageManager.get_instance()
        available = [b.name for b in mgr.get_available_backends()]
        if available:
            return DiagnosticCheck(
                name="Package Management Backends",
                status=CheckStatus.PASS,
                message=f"Detected package backends: {', '.join(available)}",
                details=f"Backends active: {', '.join(b.backend_id for b in mgr.get_available_backends())}",
            )
        return DiagnosticCheck(
            name="Package Management Backends",
            status=CheckStatus.WARN,
            message="No supported package manager (APT, Flatpak, Snap, Pacman) detected",
            fix_suggestion="Install a supported package manager to enable software management.",
        )

    @staticmethod
    def check_privilege_escalation() -> DiagnosticCheck:
        if shutil.which("pkexec") or shutil.which("kdesu") or shutil.which("sudo"):
            tool = "pkexec" if shutil.which("pkexec") else ("kdesu" if shutil.which("kdesu") else "sudo")
            return DiagnosticCheck(
                name="Privilege Escalation",
                status=CheckStatus.PASS,
                message=f"Elevation tool '{tool}' is available for package operations",
            )
        return DiagnosticCheck(
            name="Privilege Escalation",
            status=CheckStatus.WARN,
            message="No privilege elevation tool (pkexec/kdesu/sudo) detected",
            fix_suggestion="Install PolicyKit (pkexec) for system package operations.",
        )

    @staticmethod
    def check_global_shortcut() -> DiagnosticCheck:
        from lumen.service.shortcuts import KDEShortcutManager
        if KDEShortcutManager.is_kde_session():
            sc = KDEShortcutManager.get_active_shortcut()
            if sc and sc.lower() != "none":
                return DiagnosticCheck(
                    name="KDE Global Shortcut",
                    status=CheckStatus.PASS,
                    message=f"Global shortcut '{sc}' is configured in KDE Plasma",
                )
            return DiagnosticCheck(
                name="KDE Global Shortcut",
                status=CheckStatus.WARN,
                message="Global shortcut not yet registered in KDE Plasma",
                fix_suggestion="Run 'lumen setup' to configure Alt+Space shortcut.",
            )
        return DiagnosticCheck(
            name="KDE Global Shortcut",
            status=CheckStatus.INFO,
            message="Desktop session is non-KDE (configure global shortcut via window manager)",
        )

    @staticmethod
    def check_system_tray() -> DiagnosticCheck:
        try:
            from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
            app = QApplication.instance()
            if app:
                avail = QSystemTrayIcon.isSystemTrayAvailable()
                if avail:
                    return DiagnosticCheck(
                        name="System Tray Support",
                        status=CheckStatus.PASS,
                        message="KDE Plasma system tray companion is supported",
                    )
            # If no GUI app is running, check if QSystemTrayIcon class is available
            return DiagnosticCheck(
                name="System Tray Support",
                status=CheckStatus.PASS,
                message="QSystemTrayIcon bindings available (active in graphical session)",
            )
        except Exception:
            return DiagnosticCheck(
                name="System Tray Support",
                status=CheckStatus.INFO,
                message="System tray companion available when graphical desktop session is active",
            )
