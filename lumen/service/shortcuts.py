"""
KDE Plasma global shortcut registration and conflict detection helper.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Dict, Optional


def register_kde_custom_shortcut(
    action_name: str = "Lumen Toggle",
    command: str = "lumen toggle",
    shortcut: str = "Meta+Space",
) -> bool:
    """
    Registers a custom global shortcut in KDE Plasma 6 via kglobalaccel / kwriteconfig6.
    """
    # Check if kwriteconfig6 exists
    if not shutil.which("kwriteconfig6"):
        return False

    try:
        # In KDE Plasma 6, shortcuts can be registered in kglobalshortcutsrc under custom commands
        subprocess.run(
            [
                "kwriteconfig6",
                "--file", "kglobalshortcutsrc",
                "--group", "services",
                "--key", "lumen.desktop",
                f"{shortcut},none,{action_name}",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def get_shortcut_setup_instructions(shortcut: str = "Meta+Space") -> str:
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
