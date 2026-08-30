"""
KDE Plasma global shortcut registration, inspection, and conflict resolution manager.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class KDEShortcutManager:
    """Manages global shortcut configuration for KDE Plasma desktop environments."""

    @staticmethod
    def is_kde_session() -> bool:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        return "kde" in desktop or "plasma" in desktop

    @classmethod
    def get_config_tool(cls) -> Optional[str]:
        for tool in ("kwriteconfig6", "kwriteconfig5"):
            if shutil.which(tool):
                return tool
        return None

    @classmethod
    def get_read_tool(cls) -> Optional[str]:
        for tool in ("kreadconfig6", "kreadconfig5"):
            if shutil.which(tool):
                return tool
        return None

    @classmethod
    def get_active_shortcut(cls) -> Optional[str]:
        """Reads current shortcut registered for lumen.desktop in kglobalshortcutsrc."""
        read_tool = cls.get_read_tool()
        if read_tool:
            try:
                res = subprocess.run(
                    [read_tool, "--file", "kglobalshortcutsrc", "--group", "services", "--key", "lumen.desktop"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if res.returncode == 0 and res.stdout.strip():
                    parts = res.stdout.strip().split(",")
                    if parts:
                        return parts[0]
            except Exception:
                pass

        # Direct file check fallback
        kglobal_path = Path(os.path.expanduser("~/.config/kglobalshortcutsrc"))
        if kglobal_path.exists():
            try:
                text = kglobal_path.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if line.startswith("lumen.desktop="):
                        val = line.split("=", 1)[1]
                        return val.split(",")[0]
            except Exception:
                pass
        return None

    @classmethod
    def configure_shortcut(cls, shortcut: str = "Alt+Space", command: str = "lumen toggle") -> Tuple[bool, str]:
        """
        Programmatically registers the global shortcut in KDE Plasma.
        """
        config_tool = cls.get_config_tool()
        if not config_tool:
            return False, "KDE configuration tool (kwriteconfig6/5) not found"

        try:
            # 1. Register in services group
            subprocess.run(
                [
                    config_tool,
                    "--file", "kglobalshortcutsrc",
                    "--group", "services",
                    "--key", "lumen.desktop",
                    f"{shortcut},none,Lumen Launcher",
                ],
                check=False,
                timeout=5,
            )

            # 2. Reload kglobalaccel via D-Bus if available
            for qdbus_tool in ("qdbus6", "qdbus", "dbus-send"):
                if shutil.which(qdbus_tool):
                    try:
                        if "qdbus" in qdbus_tool:
                            subprocess.run(
                                [qdbus_tool, "org.kde.kglobalaccel", "/kglobalaccel", "reloadConfig"],
                                check=False,
                                timeout=3,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        break
                    except Exception:
                        pass

            return True, f"Global shortcut '{shortcut}' configured successfully for KDE Plasma."
        except Exception as e:
            return False, f"Could not configure KDE shortcut: {e}"

    @classmethod
    def remove_shortcut(cls) -> bool:
        """Removes Lumen shortcut from kglobalshortcutsrc."""
        config_tool = cls.get_config_tool()
        if not config_tool:
            return False
        try:
            subprocess.run(
                [
                    config_tool,
                    "--file", "kglobalshortcutsrc",
                    "--group", "services",
                    "--key", "lumen.desktop",
                    "none,none,Lumen Launcher",
                ],
                check=False,
                timeout=5,
            )
            return True
        except Exception:
            return False


def get_shortcut_setup_instructions(shortcut: str = "Alt+Space") -> str:
    """Returns step-by-step instructions for the user to configure the global shortcut."""
    return f"""
===================================================================
Lumen — KDE Plasma Global Shortcut Setup
===================================================================

To bind Lumen to '{shortcut}' in KDE Plasma:

1. Open KDE System Settings:
   - Run: systemsettings
   - Navigate to: Shortcuts -> Custom Shortcuts (or Shortcuts -> Add New -> Command)

2. Create a new Command shortcut:
   - Name: Lumen Launcher
   - Command: lumen toggle
   - Trigger / Shortcut: Press {shortcut}

3. Click 'Apply'.

Now pressing {shortcut} anywhere on your desktop will toggle Lumen!
===================================================================
"""
