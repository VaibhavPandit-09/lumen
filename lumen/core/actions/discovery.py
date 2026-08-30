"""
Filesystem scanner, cache, and watcher for Lumen Custom Actions.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from lumen.core.actions.manifest import ActionDefinition, load_action_manifest
from lumen.core.actions.validator import ActionValidator
from lumen.core.logging import debug, info, warning


class ActionScanner:
    """Discovers, parses, and caches user custom actions from disk."""

    def __init__(self, actions_dir: Optional[Union[str, Path]] = None):
        if actions_dir:
            self.actions_dir = Path(os.path.expanduser(str(actions_dir)))
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            self.actions_dir = Path(xdg_config) / "lumen" / "actions"

        self._cache: Dict[Path, tuple[float, ActionDefinition]] = {}
        self._watcher = None
        self._on_change_callbacks: List[Callable[[], None]] = []

    def get_actions_dir(self) -> Path:
        """Returns the resolved Path to the custom actions directory."""
        return self.actions_dir

    def ensure_actions_dir(self) -> Path:
        """Creates the actions directory if it does not already exist."""
        try:
            self.actions_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as e:
            debug("Actions", f"Could not create actions dir {self.actions_dir}: {e}")
        return self.actions_dir

    def scan(self) -> List[ActionDefinition]:
        """
        Scans actions directory, parses manifests with mtime caching, and validates definitions.
        """
        if not self.actions_dir.is_dir():
            return []

        actions: List[ActionDefinition] = []
        found_paths = set()

        try:
            entries = list(self.actions_dir.iterdir())
        except OSError as e:
            warning("Actions", f"Could not list directory {self.actions_dir}: {e}")
            return []

        for p in entries:
            # Skip hidden files
            if p.name.startswith("."):
                continue

            # Support .jsonc and .json manifests
            if p.suffix in (".jsonc", ".json") and p.is_file():
                found_paths.add(p)
                try:
                    mtime = p.stat().st_mtime
                except OSError:
                    mtime = 0.0

                if p in self._cache and self._cache[p][0] == mtime:
                    action = self._cache[p][1]
                else:
                    action = load_action_manifest(p)
                    ActionValidator.validate_action(action)
                    self._cache[p] = (mtime, action)

                if action.is_valid:
                    actions.append(action)

        # Evict deleted files from cache
        for stale in list(self._cache.keys()):
            if stale not in found_paths:
                del self._cache[stale]

        # Check for duplicate IDs across collection
        ActionValidator.validate_action_collection(actions)
        debug("Actions", f"Discovered {len(actions)} valid custom action(s) from {self.actions_dir}")
        return actions

    def setup_watcher(self, on_change: Optional[Callable[[], None]] = None) -> None:
        """Sets up filesystem watching to automatically reload actions when manifests change."""
        if on_change:
            self._on_change_callbacks.append(on_change)

        if not self.actions_dir.is_dir():
            self.ensure_actions_dir()

        try:
            from PyQt6.QtCore import QFileSystemWatcher
            if not self._watcher:
                self._watcher = QFileSystemWatcher()
                self._watcher.directoryChanged.connect(self._handle_dir_changed)
                if self.actions_dir.exists():
                    self._watcher.addPath(str(self.actions_dir))
        except Exception as e:
            debug("Actions", f"FileSystemWatcher not initialized: {e}")

    def _handle_dir_changed(self, path: str) -> None:
        """Fires registered change callbacks when the actions directory is updated."""
        debug("Actions", f"Actions directory changed on disk: {path}")
        self.scan()
        for cb in self._on_change_callbacks:
            try:
                cb()
            except Exception as e:
                error("Actions", f"Error in change callback: {e}")
