"""
Theme and styling engine integrating with KDE Plasma color schemes.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

try:
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False


@dataclass
class ThemeColors:
    is_dark: bool
    bg_color: str
    card_bg: str
    border_color: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent_color: str
    selected_bg: str
    selected_text: str
    badge_bg: str
    badge_text: str
    search_bg: str


DARK_THEME = ThemeColors(
    is_dark=True,
    bg_color="rgba(24, 26, 32, 0.96)",
    card_bg="#1E2028",
    border_color="rgba(255, 255, 255, 0.12)",
    text_primary="#F3F4F6",
    text_secondary="#9CA3AF",
    text_muted="#6B7280",
    accent_color="#3DAEE9",       # KDE Breeze Cyan/Blue
    selected_bg="#2563EB",        # Vibrant Blue selection
    selected_text="#FFFFFF",
    badge_bg="rgba(255, 255, 255, 0.08)",
    badge_text="#D1D5DB",
    search_bg="#1A1C23",
)

LIGHT_THEME = ThemeColors(
    is_dark=False,
    bg_color="rgba(250, 250, 252, 0.97)",
    card_bg="#FFFFFF",
    border_color="rgba(0, 0, 0, 0.10)",
    text_primary="#111827",
    text_secondary="#4B5563",
    text_muted="#9CA3AF",
    accent_color="#2563EB",
    selected_bg="#2563EB",
    selected_text="#FFFFFF",
    badge_bg="rgba(0, 0, 0, 0.06)",
    badge_text="#374151",
    search_bg="#F3F4F6",
)


def detect_kde_is_dark() -> bool:
    """Detects whether current KDE Plasma theme is dark."""
    # 1. Try reading kdeglobals via kreadconfig6 / kreadconfig5
    for cmd in [
        ["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
        ["kreadconfig5", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
    ]:
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=1).decode("utf-8").strip().lower()
            if output:
                if "dark" in output or "black" in output:
                    return True
                if "light" in output or "white" in output:
                    return False
        except Exception:
            continue

    # 2. Try Qt palette window text vs window background brightness
    if HAS_QT:
        app = QApplication.instance()
        if app:
            palette = app.palette()
            window_color = palette.color(QPalette.ColorRole.Window)
            # Standard luminance formula
            luminance = (0.299 * window_color.red() + 0.587 * window_color.green() + 0.114 * window_color.blue()) / 255.0
            return luminance < 0.5

    return True  # Default to dark mode


def get_theme(theme_setting: str = "auto") -> ThemeColors:
    """Returns active theme based on user preference or KDE system theme."""
    if theme_setting == "dark":
        return DARK_THEME
    elif theme_setting == "light":
        return LIGHT_THEME
    else:
        is_dark = detect_kde_is_dark()
        return DARK_THEME if is_dark else LIGHT_THEME


def generate_stylesheet(theme: ThemeColors, opacity: float = 0.98) -> str:
    """Generates complete Qt Stylesheet for Lumen widgets."""
    return f"""
    QWidget#LumenContainer {{
        background-color: {theme.bg_color};
        border: 1px solid {theme.border_color};
        border-radius: 14px;
    }}

    QLineEdit#LumenSearchBar {{
        background-color: {theme.search_bg};
        color: {theme.text_primary};
        border: 1px solid {theme.border_color};
        border-radius: 10px;
        padding: 10px 16px;
        font-size: 16px;
        font-weight: 500;
        selection-background-color: {theme.accent_color};
        selection-color: #FFFFFF;
    }}

    QLineEdit#LumenSearchBar:focus {{
        border: 1px solid {theme.accent_color};
    }}

    QLabel#LumenBreadcrumb {{
        color: {theme.accent_color};
        font-size: 13px;
        font-weight: bold;
        padding-left: 4px;
        margin-bottom: 2px;
    }}

    QListWidget#LumenResultList {{
        background-color: transparent;
        border: none;
        outline: none;
        padding: 4px 0px;
    }}

    QListWidget#LumenResultList::item {{
        background-color: transparent;
        border-radius: 8px;
        padding: 6px 10px;
        margin: 2px 4px;
        color: {theme.text_primary};
    }}

    QListWidget#LumenResultList::item:selected {{
        background-color: {theme.selected_bg};
        color: {theme.selected_text};
    }}

    QListWidget#LumenResultList::item:hover:!selected {{
        background-color: {theme.badge_bg};
    }}

    QLabel#LumenFooter {{
        color: {theme.text_muted};
        font-size: 11px;
        padding: 4px 8px;
    }}
    """
