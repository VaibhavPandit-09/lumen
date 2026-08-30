"""
JSONC configuration parser, schema validation, and config management.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from lumen.core.models import CommandItem


def strip_jsonc_comments(jsonc_text: str) -> str:
    """Removes single-line (//) and multi-line (/* */) comments from JSONC string."""
    result = []
    i = 0
    length = len(jsonc_text)
    in_string = False
    string_char = ""
    escape = False

    while i < length:
        ch = jsonc_text[i]

        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            i += 1
            continue

        if ch in ('"', "'"):
            in_string = True
            string_char = ch
            result.append(ch)
            i += 1
            continue

        # Check for line comment //
        if ch == "/" and i + 1 < length and jsonc_text[i + 1] == "/":
            i += 2
            while i < length and jsonc_text[i] not in ("\n", "\r"):
                i += 1
            continue

        # Check for block comment /* */
        if ch == "/" and i + 1 < length and jsonc_text[i + 1] == "*":
            i += 2
            while i + 1 < length and not (jsonc_text[i] == "*" and jsonc_text[i + 1] == "/"):
                i += 1
            i += 2
            continue

        result.append(ch)
        i += 1

    cleaned = "".join(result)
    # Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
    return cleaned


def parse_jsonc(text: str) -> Dict[str, Any]:
    """Parses a JSONC text into a Python dictionary."""
    cleaned = strip_jsonc_comments(text)
    if not cleaned.strip():
        return {}
    return json.loads(cleaned)


DEFAULT_CONFIG_JSONC = """// Lumen Main Configuration
// An agent-friendly command launcher for KDE Plasma
{
  "$schema": "https://raw.githubusercontent.com/VaibhavPandit-09/lumen/main/lumen/core/schema.json",

  // Global shortcut to toggle Lumen
  "shortcut": "Meta+Space",

  // Theme mode: "auto" (follows KDE Breeze palette), "dark", or "light"
  "theme": "auto",

  // Window width in pixels
  "window_width": 680,

  // Maximum number of visible search items
  "max_results": 9,

  // Window opacity (0.5 to 1.0)
  "opacity": 0.98,

  // Display category badges in search result rows
  "show_badges": true,

  // Enable/disable individual search providers
  "providers": {
    "applications": true,
    "commands": true,
    "system_actions": true,
    "locations": true,
    "calculator": true,
    "recent_files": true,
    "clipboard": true,
    "web_search": true
  },

  // List of .desktop application IDs or names to hide from search results
  "hidden_applications": [],

  // URL template for fallback web search (%s will be replaced with your query)
  "web_search_engine": "https://duckduckgo.com/?q=%s",

  // Automatically calculate math expressions typed in search bar
  "calculator_auto_evaluate": true
}
"""

DEFAULT_COMMANDS_JSONC = """// Lumen User & Agent Commands
// Define custom commands, scripts, workflows, and nested submenus here.
{
  "$schema": "https://raw.githubusercontent.com/VaibhavPandit-09/lumen/main/lumen/core/schema.json",
  "commands": [
    {
      "name": "Development Menu",
      "description": "Developer tools, servers, and project shortcuts",
      "icon": "applications-development",
      "category": "Development",
      "subcommands": [
        {
          "name": "Restart Docker Containers",
          "description": "Restart local docker compose services",
          "icon": "docker",
          "command": "docker compose restart",
          "terminal": false
        },
        {
          "name": "Show Docker Logs",
          "description": "Follow docker container logs in terminal",
          "icon": "utilities-terminal",
          "command": "docker compose logs -f",
          "terminal": true
        },
        {
          "name": "Git Status & Fetch",
          "description": "Fetch remotes and show git status",
          "icon": "vcs-branch",
          "command": "git fetch --all && git status",
          "terminal": true
        }
      ]
    },
    {
      "name": "Edit Lumen Commands",
      "description": "Open commands.jsonc in default text editor",
      "icon": "document-edit",
      "category": "Lumen",
      "command": "xdg-open ~/.config/lumen/commands.jsonc"
    },
    {
      "name": "Edit Lumen Config",
      "description": "Open config.jsonc in default text editor",
      "icon": "preferences-system",
      "category": "Lumen",
      "command": "xdg-open ~/.config/lumen/config.jsonc"
    }
  ]
}
"""


@dataclass
class LumenConfig:
    config_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) / "lumen"
    )
    shortcut: str = "Meta+Space"
    theme: str = "auto"
    window_width: int = 680
    max_results: int = 9
    opacity: float = 0.98
    show_badges: bool = True
    providers: Dict[str, bool] = field(
        default_factory=lambda: {
            "applications": True,
            "commands": True,
            "system_actions": True,
            "locations": True,
            "calculator": True,
            "recent_files": True,
            "clipboard": True,
            "web_search": True,
        }
    )
    hidden_applications: List[str] = field(default_factory=list)
    web_search_engine: str = "https://duckduckgo.com/?q=%s"
    calculator_auto_evaluate: bool = True
    commands: List[CommandItem] = field(default_factory=list)

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.jsonc"

    @property
    def commands_file(self) -> Path:
        return self.config_dir / "commands.jsonc"

    def ensure_config_files(self) -> None:
        """Creates default configuration files if they do not exist."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            if not self.config_file.exists():
                self.config_file.write_text(DEFAULT_CONFIG_JSONC, encoding="utf-8")

            if not self.commands_file.exists():
                self.commands_file.write_text(DEFAULT_COMMANDS_JSONC, encoding="utf-8")
        except (OSError, PermissionError) as e:
            # Running in read-only environment or sandbox, populate default commands in-memory
            if not self.commands:
                try:
                    cmd_data = parse_jsonc(DEFAULT_COMMANDS_JSONC)
                    if isinstance(cmd_data.get("commands"), list):
                        self.commands = [
                            CommandItem.from_dict(c)
                            for c in cmd_data["commands"]
                            if isinstance(c, dict)
                        ]
                except Exception:
                    pass

    def load(self) -> "LumenConfig":
        """Loads configuration and commands from disk or defaults."""
        self.ensure_config_files()

        # If no commands loaded yet, parse defaults
        if not self.commands:
            try:
                cmd_data = parse_jsonc(DEFAULT_COMMANDS_JSONC)
                if isinstance(cmd_data.get("commands"), list):
                    self.commands = [
                        CommandItem.from_dict(c)
                        for c in cmd_data["commands"]
                        if isinstance(c, dict)
                    ]
            except Exception:
                pass

        # Load main config
        try:
            if self.config_file.exists():
                text = self.config_file.read_text(encoding="utf-8")
                data = parse_jsonc(text)
                self.shortcut = str(data.get("shortcut", self.shortcut))
                self.theme = str(data.get("theme", self.theme))
                self.window_width = int(data.get("window_width", self.window_width))
                self.max_results = int(data.get("max_results", self.max_results))
                self.opacity = float(data.get("opacity", self.opacity))
                self.show_badges = bool(data.get("show_badges", self.show_badges))
                if isinstance(data.get("providers"), dict):
                    self.providers.update(data["providers"])
                if isinstance(data.get("hidden_applications"), list):
                    self.hidden_applications = [str(x) for x in data["hidden_applications"]]
                self.web_search_engine = str(data.get("web_search_engine", self.web_search_engine))
                self.calculator_auto_evaluate = bool(
                    data.get("calculator_auto_evaluate", self.calculator_auto_evaluate)
                )
                if "commands" in data and isinstance(data["commands"], list):
                    self.commands = [CommandItem.from_dict(c) for c in data["commands"] if isinstance(c, dict)]
        except Exception as e:
            print(f"[Lumen Config] Warning: Failed to parse config.jsonc ({e})")

        # Load separate commands.jsonc if exists
        try:
            if self.commands_file.exists():
                cmd_text = self.commands_file.read_text(encoding="utf-8")
                cmd_data = parse_jsonc(cmd_text)
                if isinstance(cmd_data.get("commands"), list):
                    loaded_cmds = [
                        CommandItem.from_dict(c) for c in cmd_data["commands"] if isinstance(c, dict)
                    ]
                    # Append commands from commands.jsonc avoiding duplicate names
                    existing_names = {c.name for c in self.commands}
                    for cmd in loaded_cmds:
                        if cmd.name not in existing_names:
                            self.commands.append(cmd)
        except Exception as e:
            print(f"[Lumen Config] Warning: Failed to parse commands.jsonc ({e})")

        return self

    def add_command(self, cmd: CommandItem) -> None:
        """Appends a new command and persists to commands.jsonc."""
        self.commands.append(cmd)
        self.save_commands()

    def save_commands(self) -> None:
        """Persists current commands list to commands.jsonc."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "$schema": "https://raw.githubusercontent.com/VaibhavPandit-09/lumen/main/lumen/core/schema.json",
                "commands": [c.to_dict() for c in self.commands],
            }
            self.commands_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except (OSError, PermissionError) as e:
            print(f"[Lumen Config] Warning: Could not write to {self.commands_file}: {e}")
