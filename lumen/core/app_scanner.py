"""
XDG .desktop file scanner, parser, and live filesystem watcher.
"""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from lumen.core.logging import debug, error, info
from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import launch_desktop_file

try:
    from PyQt6.QtCore import QFileSystemWatcher, QObject, pyqtSignal
    HAS_QT = True
except ImportError:
    HAS_QT = False


def get_desktop_directories() -> List[Path]:
    """Returns all standard XDG application directories to search in priority order."""
    dirs: List[Path] = []

    # 1. User local applications (highest priority)
    xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    user_app_dir = Path(xdg_data_home) / "applications"
    if user_app_dir.is_dir():
        dirs.append(user_app_dir)

    # 2. Flatpak user applications
    user_flatpak = Path(os.path.expanduser("~/.local/share/flatpak/exports/share/applications"))
    if user_flatpak.is_dir() and user_flatpak not in dirs:
        dirs.append(user_flatpak)

    # 3. System application directories
    xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    for d in xdg_data_dirs:
        if d.strip():
            app_dir = Path(d.strip()) / "applications"
            if app_dir.is_dir() and app_dir not in dirs:
                dirs.append(app_dir)

    # 4. System Flatpak & Snap applications
    for extra in [
        Path("/var/lib/flatpak/exports/share/applications"),
        Path("/var/lib/snapd/desktop/applications"),
    ]:
        if extra.is_dir() and extra not in dirs:
            dirs.append(extra)

    # 5. Fallback standard dirs if not added
    for std in [Path("/usr/share/applications"), Path("/usr/local/share/applications")]:
        if std.is_dir() and std not in dirs:
            dirs.append(std)

    return dirs


class AppScanner:
    """Discovers and parses .desktop application files with live filesystem watching."""

    def __init__(self, hidden_applications: Optional[List[str]] = None):
        self.hidden_applications: Set[str] = set(hidden_applications or [])
        self.cached_results: List[SearchResult] = []
        self._parsed_cache: Dict[str, tuple[float, List[SearchResult]]] = {}
        self._watcher: Optional[Any] = None
        self._change_callbacks: List[Callable[[], None]] = []

    def set_hidden_applications(self, hidden: List[str]) -> None:
        self.hidden_applications = set(hidden)

    def add_change_callback(self, callback: Callable[[], None]) -> None:
        self._change_callbacks.append(callback)

    def _notify_change(self) -> None:
        for cb in self._change_callbacks:
            try:
                cb()
            except Exception:
                pass

    def setup_watcher(self) -> None:
        """Sets up live directory monitoring using QFileSystemWatcher if available and event loop exists."""
        if not HAS_QT:
            return

        try:
            from PyQt6.QtCore import QCoreApplication
            if not QCoreApplication.instance():
                return

            self._watcher = QFileSystemWatcher()
            for d in get_desktop_directories():
                if d.exists():
                    self._watcher.addPath(str(d))
            self._watcher.directoryChanged.connect(lambda _: self._on_fs_change())
            self._watcher.fileChanged.connect(lambda _: self._on_fs_change())
        except Exception:
            pass

    def _on_fs_change(self) -> None:
        self.scan()
        self._notify_change()

    def parse_desktop_file(self, file_path: Path) -> List[SearchResult]:
        """Parses a single .desktop file and returns main result and any desktop actions."""
        results: List[SearchResult] = []

        config = configparser.RawConfigParser(interpolation=None, strict=False)
        try:
            config.read(str(file_path), encoding="utf-8")
        except Exception:
            return results

        if not config.has_section("Desktop Entry"):
            return results

        entry = config["Desktop Entry"]

        # Check application type
        app_type = entry.get("Type", "").strip()
        if app_type and app_type != "Application":
            return results

        # Check visibility
        if entry.get("NoDisplay", "").lower() == "true":
            return results
        if entry.get("Hidden", "").lower() == "true":
            return results

        # Check environment restrictions
        only_show_in = entry.get("OnlyShowIn", "").split(";")
        not_show_in = entry.get("NotShowIn", "").split(";")
        desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "KDE").upper()

        if any(only_show_in) and not any(env.strip().upper() in desktop_env for env in only_show_in if env.strip()):
            return results
        if any(env.strip().upper() in desktop_env for env in not_show_in if env.strip()):
            return results

        name = entry.get("Name", "").strip()
        if not name:
            return results

        file_id = file_path.name
        # Check hidden list
        if file_id in self.hidden_applications or name in self.hidden_applications:
            return results

        generic_name = entry.get("GenericName", "").strip()
        comment = entry.get("Comment", "").strip()
        exec_cmd = entry.get("Exec", "").strip()
        if not exec_cmd:
            return results

        icon_name = entry.get("Icon", "application-x-executable").strip()
        terminal = entry.get("Terminal", "").lower() == "true"
        categories = [c.strip() for c in entry.get("Categories", "").split(";") if c.strip()]
        keywords = [k.strip() for k in entry.get("Keywords", "").split(";") if k.strip()]

        subtitle = generic_name or comment or ("Terminal application" if terminal else "")

        main_result = SearchResult(
            id=f"app:{file_id}",
            title=name,
            subtitle=subtitle,
            category=ItemCategory.APPLICATION.value,
            icon_name=icon_name,
            action=lambda cmd=exec_cmd, term=terminal: launch_desktop_file(cmd, terminal=term),
            badge="App",
            keywords=keywords + categories,
            context={"file_path": str(file_path), "exec": exec_cmd, "desktop_id": file_id},
        )
        results.append(main_result)

        # Parse Desktop Actions (e.g. New Window, Incognito, etc.)
        actions_str = entry.get("Actions", "").strip()
        if actions_str:
            action_keys = [a.strip() for a in actions_str.split(";") if a.strip()]
            for act_key in action_keys:
                section_name = f"Desktop Action {act_key}"
                if config.has_section(section_name):
                    act_section = config[section_name]
                    act_name = act_section.get("Name", "").strip()
                    act_exec = act_section.get("Exec", "").strip()
                    act_icon = act_section.get("Icon", icon_name).strip()
                    if act_name and act_exec:
                        results.append(
                            SearchResult(
                                id=f"app_action:{file_id}:{act_key}",
                                title=f"{name} — {act_name}",
                                subtitle=f"Action for {name}",
                                category=ItemCategory.APPLICATION.value,
                                icon_name=act_icon,
                                action=lambda cmd=act_exec, term=terminal: launch_desktop_file(cmd, terminal=term),
                                badge="Action",
                                keywords=keywords + [act_name, name],
                                context={"parent_app": name, "exec": act_exec},
                            )
                        )

        return results

    def scan(self) -> List[SearchResult]:
        """Scans all application directories and caches search results with mtime optimization."""
        discovered: Dict[str, SearchResult] = {}
        seen_file_ids: Set[str] = set()

        for directory in get_desktop_directories():
            if not directory.is_dir():
                continue
            try:
                for file_path in directory.glob("*.desktop"):
                    file_id = file_path.name
                    # Deduplicate: if we already saw this desktop file ID in a higher-priority folder, skip
                    if file_id in seen_file_ids:
                        continue

                    # Check mtime cache
                    try:
                        mtime = file_path.stat().st_mtime
                    except OSError:
                        mtime = 0.0

                    cached_entry = self._parsed_cache.get(str(file_path))
                    if cached_entry and cached_entry[0] == mtime:
                        parsed_list = cached_entry[1]
                    else:
                        parsed_list = self.parse_desktop_file(file_path)
                        self._parsed_cache[str(file_path)] = (mtime, parsed_list)

                    if parsed_list:
                        seen_file_ids.add(file_id)
                        for item in parsed_list:
                            if item.id not in discovered:
                                discovered[item.id] = item
            except Exception as e:
                error("AppScanner", f"Error scanning directory {directory}", exc=e)

        self.cached_results = list(discovered.values())
        debug("AppScanner", f"Scan complete. Indexed {len(self.cached_results)} applications & actions.")
        return self.cached_results
