"""
KDE Plasma 6 system actions provider (Lock, Logout, Suspend, Restart, Shutdown, Settings).
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Callable, List, Optional

from lumen.core.fuzzy import score_item
from lumen.core.models import ItemCategory, SearchResult
from lumen.providers.base import BaseProvider


def _run_action(cmd_list: List[List[str]]) -> bool:
    """Tries executing commands in order until one succeeds."""
    for cmd in cmd_list:
        binary = cmd[0]
        if shutil.which(binary):
            try:
                subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
                return True
            except Exception:
                continue
    return False


def action_lock_screen() -> bool:
    return _run_action([
        ["qdbus6", "org.freedesktop.ScreenSaver", "/ScreenSaver", "Lock"],
        ["qdbus", "org.freedesktop.ScreenSaver", "/ScreenSaver", "Lock"],
        ["loginctl", "lock-session"],
    ])


def action_logout() -> bool:
    return _run_action([
        ["qdbus6", "org.kde.Shutdown", "/Shutdown", "logout"],
        ["qdbus6", "org.kde.ksmserver", "/KSMServer", "org.kde.KSMServerInterface.logout", "0", "0", "0"],
        ["qdbus", "org.kde.Shutdown", "/Shutdown", "logout"],
        ["loginctl", "terminate-session", "self"],
    ])


def action_suspend() -> bool:
    return _run_action([
        ["qdbus6", "org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager.Suspend", "false"],
        ["systemctl", "suspend"],
        ["loginctl", "suspend"],
    ])


def action_reboot() -> bool:
    return _run_action([
        ["qdbus6", "org.kde.Shutdown", "/Shutdown", "logoutAndReboot"],
        ["systemctl", "reboot"],
        ["loginctl", "reboot"],
    ])


def action_shutdown() -> bool:
    return _run_action([
        ["qdbus6", "org.kde.Shutdown", "/Shutdown", "logoutAndShutdown"],
        ["systemctl", "poweroff"],
        ["loginctl", "poweroff"],
    ])


def action_open_settings(kcm: Optional[str] = None) -> bool:
    if kcm:
        return _run_action([
            ["systemsettings", kcm],
            ["kcmshell6", kcm],
            ["kcmshell5", kcm],
            ["systemsettings"],
        ])
    return _run_action([["systemsettings"]])


class SystemActionsProvider(BaseProvider):
    """Provides searchable KDE Plasma 6 system actions and settings shortcuts."""

    def __init__(self, enabled: bool = True):
        super().__init__("system_actions", enabled=enabled)
        self.actions: List[SearchResult] = []

    def initialize(self) -> None:
        self.actions = [
            SearchResult(
                id="sys:lock",
                title="Lock Screen",
                subtitle="Lock the current KDE session",
                category=ItemCategory.SYSTEM.value,
                icon_name="system-lock-screen",
                action=action_lock_screen,
                badge="System",
                keywords=["lock", "screen", "session", "sleep"],
            ),
            SearchResult(
                id="sys:logout",
                title="Log Out",
                subtitle="End current user session",
                category=ItemCategory.SYSTEM.value,
                icon_name="system-log-out",
                action=action_logout,
                badge="System",
                keywords=["logout", "exit", "sign out", "leave"],
            ),
            SearchResult(
                id="sys:suspend",
                title="Suspend / Sleep",
                subtitle="Put computer to sleep (RAM sleep)",
                category=ItemCategory.SYSTEM.value,
                icon_name="system-suspend",
                action=action_suspend,
                badge="System",
                keywords=["suspend", "sleep", "standby"],
            ),
            SearchResult(
                id="sys:restart",
                title="Restart / Reboot",
                subtitle="Reboot computer",
                category=ItemCategory.SYSTEM.value,
                icon_name="system-reboot",
                action=action_reboot,
                badge="System",
                keywords=["restart", "reboot", "reset"],
            ),
            SearchResult(
                id="sys:shutdown",
                title="Shut Down / Power Off",
                subtitle="Turn off computer completely",
                category=ItemCategory.SYSTEM.value,
                icon_name="system-shutdown",
                action=action_shutdown,
                badge="System",
                keywords=["shutdown", "power off", "turn off", "halt"],
            ),
            SearchResult(
                id="sys:settings",
                title="System Settings",
                subtitle="Open KDE Plasma System Settings",
                category=ItemCategory.SYSTEM.value,
                icon_name="preferences-system",
                action=lambda: action_open_settings(),
                badge="Settings",
                keywords=["settings", "preferences", "control center", "config"],
            ),
            SearchResult(
                id="sys:display_settings",
                title="Display Configuration",
                subtitle="Configure monitors, resolution, and refresh rate",
                category=ItemCategory.SYSTEM.value,
                icon_name="preferences-desktop-display",
                action=lambda: action_open_settings("kcm_kscreen"),
                badge="Settings",
                keywords=["display", "screen", "monitor", "resolution", "scaling", "multi-monitor"],
            ),
            SearchResult(
                id="sys:audio_settings",
                title="Audio / Sound Settings",
                subtitle="Configure speakers, microphones, and volume levels",
                category=ItemCategory.SYSTEM.value,
                icon_name="preferences-desktop-sound",
                action=lambda: action_open_settings("kcm_pulseaudio"),
                badge="Settings",
                keywords=["audio", "sound", "volume", "microphone", "speaker"],
            ),
            SearchResult(
                id="sys:network_settings",
                title="Network Settings",
                subtitle="Configure Wi-Fi, Ethernet, and VPN connections",
                category=ItemCategory.SYSTEM.value,
                icon_name="preferences-system-network",
                action=lambda: action_open_settings("kcm_networkmanagement"),
                badge="Settings",
                keywords=["network", "wifi", "ethernet", "internet", "vpn", "ip"],
            ),
            SearchResult(
                id="sys:bluetooth_settings",
                title="Bluetooth Settings",
                subtitle="Pair and manage Bluetooth devices",
                category=ItemCategory.SYSTEM.value,
                icon_name="preferences-system-bluetooth",
                action=lambda: action_open_settings("kcm_bluetooth"),
                badge="Settings",
                keywords=["bluetooth", "pair", "wireless", "devices"],
            ),
        ]

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled:
            return []

        results: List[SearchResult] = []
        q = query.strip()

        for item in self.actions:
            matched, score = score_item(
                query=q,
                title=item.title,
                subtitle=item.subtitle,
                keywords=item.keywords,
                category=item.category,
            )
            if matched and score > 0:
                scored = SearchResult(
                    id=item.id,
                    title=item.title,
                    subtitle=item.subtitle,
                    category=item.category,
                    icon_name=item.icon_name,
                    score=score + 10.0,
                    action=item.action,
                    subcommands=item.subcommands,
                    badge=item.badge,
                    keywords=item.keywords,
                    shortcut_hint=item.shortcut_hint,
                    context=item.context,
                )
                results.append(scored)

        return results
