"""
Validation engine for Lumen Custom Actions with actionable diagnostics.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from lumen.core.actions.manifest import ActionDefinition


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Represents a diagnostic issue found during action validation."""
    severity: IssueSeverity
    message: str
    field: Optional[str] = None


class ActionValidator:
    """Validates ActionDefinition contracts and executables."""

    ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    @classmethod
    def validate_action(cls, action: ActionDefinition) -> List[ValidationIssue]:
        """Performs comprehensive validation on a single ActionDefinition."""
        issues: List[ValidationIssue] = []

        # Include prior parsing errors
        for err in action.validation_errors:
            issues.append(ValidationIssue(IssueSeverity.ERROR, err))

        # 1. Validate ID
        if not action.id:
            issues.append(ValidationIssue(IssueSeverity.ERROR, "Action 'id' is required", field="id"))
        elif not cls.ID_PATTERN.match(action.id):
            issues.append(
                ValidationIssue(
                    IssueSeverity.ERROR,
                    f"Action 'id' '{action.id}' must contain only alphanumeric characters, dashes, and underscores",
                    field="id",
                )
            )

        # 2. Validate Name
        if not action.name:
            issues.append(ValidationIssue(IssueSeverity.ERROR, "Action 'name' is required and cannot be empty", field="name"))

        # 3. Validate Executable definition
        if not action.exec:
            issues.append(ValidationIssue(IssueSeverity.ERROR, "Action 'exec' definition is required", field="exec"))
        else:
            first_cmd = action.exec[0] if isinstance(action.exec, list) else action.exec.split()[0]
            # Check executable existence in PATH or absolute path
            expanded_cmd = os.path.expanduser(first_cmd)
            if os.path.isabs(expanded_cmd):
                if not os.path.exists(expanded_cmd):
                    issues.append(
                        ValidationIssue(
                            IssueSeverity.ERROR,
                            f"Executable does not exist: '{first_cmd}'",
                            field="exec",
                        )
                    )
                elif not os.access(expanded_cmd, os.X_OK):
                    issues.append(
                        ValidationIssue(
                            IssueSeverity.WARNING,
                            f"File exists but may not be executable: '{first_cmd}'",
                            field="exec",
                        )
                    )
            else:
                # Look up in system PATH
                if not shutil.which(first_cmd):
                    issues.append(
                        ValidationIssue(
                            IssueSeverity.WARNING,
                            f"Executable '{first_cmd}' not found in current system PATH",
                            field="exec",
                        )
                    )

        # 4. Validate CWD
        if action.cwd:
            expanded_cwd = os.path.expanduser(action.cwd)
            if not os.path.isdir(expanded_cwd):
                issues.append(
                    ValidationIssue(
                        IssueSeverity.WARNING,
                        f"Working directory does not exist: '{action.cwd}'",
                        field="cwd",
                    )
                )

        # 5. Validate Timeout
        if action.timeout_seconds <= 0 or action.timeout_seconds > 300:
            issues.append(
                ValidationIssue(
                    IssueSeverity.ERROR,
                    f"Timeout must be between 1 and 300 seconds (got {action.timeout_seconds})",
                    field="timeout_seconds",
                )
            )

        # 6. Validate Arguments Schema
        seen_arg_names = set()
        for arg in action.args_schema:
            if not arg.name:
                issues.append(ValidationIssue(IssueSeverity.ERROR, "Argument name cannot be empty", field="args"))
            elif arg.name in seen_arg_names:
                issues.append(
                    ValidationIssue(
                        IssueSeverity.ERROR,
                        f"Duplicate argument name '{arg.name}' in action '{action.id}'",
                        field="args",
                    )
                )
            seen_arg_names.add(arg.name)

            if arg.choices and arg.default and arg.default not in arg.choices:
                issues.append(
                    ValidationIssue(
                        IssueSeverity.WARNING,
                        f"Default value '{arg.default}' for argument '{arg.name}' is not in allowed choices",
                        field="args",
                    )
                )

        # Update action validity state
        has_errors = any(i.severity == IssueSeverity.ERROR for i in issues)
        action.is_valid = not has_errors
        return issues

    @classmethod
    def validate_action_collection(cls, actions: List[ActionDefinition]) -> List[ValidationIssue]:
        """Validates a collection of actions, including duplicate ID detection."""
        all_issues: List[ValidationIssue] = []
        seen_ids: dict[str, Path] = {}

        for action in actions:
            action_issues = cls.validate_action(action)
            all_issues.extend(action_issues)

            if action.id:
                if action.id in seen_ids:
                    prev_src = seen_ids[action.id]
                    curr_src = action.source_path or "unknown"
                    all_issues.append(
                        ValidationIssue(
                            IssueSeverity.ERROR,
                            f"Duplicate action ID '{action.id}' found in '{curr_src}' (already defined in '{prev_src}')",
                            field="id",
                        )
                    )
                else:
                    seen_ids[action.id] = action.source_path or Path(action.id)

        return all_issues
