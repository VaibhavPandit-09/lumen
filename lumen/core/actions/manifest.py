"""
ActionDefinition dataclass and manifest parser for Lumen Custom Actions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lumen.core.config import parse_jsonc
from lumen.core.logging import debug, error, warning


@dataclass
class ActionArgument:
    """Defines an argument accepted by a custom action."""
    name: str
    description: str = ""
    default: Optional[str] = None
    choices: List[str] = field(default_factory=list)
    required: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ActionArgument:
        return cls(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            default=data.get("default"),
            choices=[str(c) for c in data.get("choices", [])],
            required=bool(data.get("required", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "required": self.required,
        }
        if self.default is not None:
            res["default"] = self.default
        if self.choices:
            res["choices"] = self.choices
        return res


@dataclass
class ActionDefinition:
    """Declarative contract for a user/agent-created custom action in Lumen."""
    id: str
    name: str
    description: str = ""
    icon: str = "system-run"
    category: str = "Actions"
    keywords: List[str] = field(default_factory=list)
    exec: Union[List[str], str] = field(default_factory=list)
    cwd: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    terminal: bool = False
    confirm: bool = False
    confirm_message: str = ""
    timeout_seconds: int = 15
    args_schema: List[ActionArgument] = field(default_factory=list)
    source_path: Optional[Path] = None
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_path: Optional[Path] = None) -> ActionDefinition:
        """Parses an ActionDefinition from a dictionary."""
        raw_exec = data.get("exec", [])
        if isinstance(raw_exec, str):
            exec_val = raw_exec
        elif isinstance(raw_exec, list):
            exec_val = [str(x) for x in raw_exec]
        else:
            exec_val = []

        args = []
        if isinstance(data.get("args"), list):
            for a in data["args"]:
                if isinstance(a, dict):
                    args.append(ActionArgument.from_dict(a))

        return cls(
            id=str(data.get("id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            description=str(data.get("description", "")).strip(),
            icon=str(data.get("icon", "system-run")).strip() or "system-run",
            category=str(data.get("category", "Actions")).strip() or "Actions",
            keywords=[str(k).strip() for k in data.get("keywords", []) if str(k).strip()],
            exec=exec_val,
            cwd=str(data.get("cwd", "")).strip() or None,
            env={str(k): str(v) for k, v in data.get("env", {}).items()} if isinstance(data.get("env"), dict) else {},
            terminal=bool(data.get("terminal", False)),
            confirm=bool(data.get("confirm", False)),
            confirm_message=str(data.get("confirm_message", "")).strip(),
            timeout_seconds=int(data.get("timeout_seconds", 15)),
            args_schema=args,
            source_path=source_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the action definition to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "keywords": self.keywords,
            "exec": self.exec,
            "cwd": self.cwd,
            "env": self.env,
            "terminal": self.terminal,
            "confirm": self.confirm,
            "confirm_message": self.confirm_message,
            "timeout_seconds": self.timeout_seconds,
            "args": [a.to_dict() for a in self.args_schema],
        }


def load_action_manifest(path: Path) -> ActionDefinition:
    """
    Loads and parses an action manifest file (.jsonc or .json).
    Returns an ActionDefinition object (marked is_valid=False if parsing fails).
    """
    if not path.is_file():
        action = ActionDefinition(id=path.stem, name=path.stem, is_valid=False)
        action.validation_errors.append(f"Manifest file not found: {path}")
        return action

    try:
        content = path.read_text(encoding="utf-8")
        data = parse_jsonc(content)
        if not isinstance(data, dict):
            action = ActionDefinition(id=path.stem, name=path.stem, is_valid=False, source_path=path)
            action.validation_errors.append("Manifest root must be a JSON object")
            return action

        action = ActionDefinition.from_dict(data, source_path=path)
        return action
    except Exception as e:
        debug("Actions", f"Failed to parse manifest {path}: {e}")
        action = ActionDefinition(id=path.stem, name=path.stem, is_valid=False, source_path=path)
        action.validation_errors.append(f"JSON syntax error in manifest: {e}")
        return action
