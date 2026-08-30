"""
Safe execution engine and process manager for Lumen Custom Actions.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from lumen.core.actions.manifest import ActionDefinition
from lumen.core.logging import debug, error, info, warning
from lumen.core.runner import launch_in_terminal


@dataclass
class ActionContext:
    """Execution context passed to a custom action."""
    action_id: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    query: str = ""
    extra_env: Dict[str, str] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Outcome of an action execution."""
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""
    execution_time_ms: float = 0.0


class ActionExecutor:
    """Executes custom actions safely without shell injection."""

    @classmethod
    def build_argv(cls, action: ActionDefinition, context: Optional[ActionContext] = None) -> List[str]:
        """Constructs an argument vector (argv) without shell string concatenation."""
        raw_exec = action.exec
        if isinstance(raw_exec, str):
            argv = shlex.split(raw_exec)
        else:
            argv = list(raw_exec)

        if not argv:
            return []

        # Expand ~ in command
        argv[0] = os.path.expanduser(argv[0])

        # If context has arguments, substitute placeholder tokens or append
        if context and context.args:
            resolved_argv: List[str] = []
            for token in argv:
                for k, v in context.args.items():
                    token = token.replace(f"${{{k}}}", str(v)).replace(f"${k}", str(v))
                resolved_argv.append(token)
            return resolved_argv

        return argv

    @classmethod
    def execute(
        cls,
        action: ActionDefinition,
        context: Optional[ActionContext] = None,
        timeout: Optional[int] = None,
    ) -> ActionResult:
        """
        Executes a custom action synchronously or as a detached process.
        Guarantees shell=False to eliminate command injection vectors.
        """
        argv = cls.build_argv(action, context)
        if not argv:
            return ActionResult(success=False, error_message="Empty execution command")

        # Check if terminal execution is requested
        if action.terminal:
            debug("Actions", f"Launching in terminal: {argv}")
            ok = launch_in_terminal(argv)
            return ActionResult(success=ok, exit_code=0 if ok else 1)

        # Prepare working directory
        cwd = None
        if action.cwd:
            cwd = os.path.expanduser(action.cwd)
            if not os.path.isdir(cwd):
                warning("Actions", f"Configured cwd does not exist: {cwd}")
                cwd = None

        # Prepare environment
        env = os.environ.copy()
        if action.env:
            env.update(action.env)
        if context and context.extra_env:
            env.update(context.extra_env)

        timeout_sec = timeout or action.timeout_seconds
        start_time = time.monotonic()

        debug("Actions", f"Executing action '{action.id}' (timeout: {timeout_sec}s): {argv[0]}")

        try:
            process = subprocess.run(
                argv,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                shell=False,
            )
            elapsed = (time.monotonic() - start_time) * 1000
            success = process.returncode == 0

            if not success:
                debug(
                    "Actions",
                    f"Action '{action.id}' returned code {process.returncode}. Stderr: {process.stderr.strip()}",
                )

            return ActionResult(
                success=success,
                exit_code=process.returncode,
                stdout=process.stdout.strip(),
                stderr=process.stderr.strip(),
                error_message=process.stderr.strip() if not success else "",
                execution_time_ms=elapsed,
            )

        except subprocess.TimeoutExpired:
            elapsed = (time.monotonic() - start_time) * 1000
            err = f"Action '{action.id}' timed out after {timeout_sec} seconds"
            warning("Actions", err)
            return ActionResult(
                success=False,
                exit_code=-1,
                error_message=err,
                execution_time_ms=elapsed,
            )

        except FileNotFoundError as e:
            elapsed = (time.monotonic() - start_time) * 1000
            err = f"Executable not found: '{argv[0]}'"
            warning("Actions", err)
            return ActionResult(
                success=False,
                exit_code=127,
                error_message=err,
                execution_time_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.monotonic() - start_time) * 1000
            err = f"Execution failed: {e}"
            error("Actions", err, exc=e)
            return ActionResult(
                success=False,
                exit_code=1,
                error_message=err,
                execution_time_ms=elapsed,
            )
