"""
Logging and diagnostic subsystem for Lumen.
Supports verbose debug mode with module-specific tags while protecting user privacy.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

_DEBUG_ENABLED: bool = os.environ.get("LUMEN_DEBUG", "").lower() in ("1", "true", "yes")


def set_debug(enabled: bool) -> None:
    """Enables or disables verbose debug logging."""
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = enabled


def is_debug() -> bool:
    """Returns whether debug logging is active."""
    return _DEBUG_ENABLED


def _format_timestamp() -> str:
    return time.strftime("%H:%M:%S")


def debug(tag: str, message: str) -> None:
    """Logs a debug diagnostic message if debug mode is enabled."""
    if _DEBUG_ENABLED:
        sys.stderr.write(f"[{_format_timestamp()}] [DEBUG] [{tag}] {message}\n")
        sys.stderr.flush()


def info(tag: str, message: str) -> None:
    """Logs an informational message."""
    sys.stderr.write(f"[{_format_timestamp()}] [INFO]  [{tag}] {message}\n")
    sys.stderr.flush()


def warning(tag: str, message: str) -> None:
    """Logs a warning message."""
    sys.stderr.write(f"[{_format_timestamp()}] [WARN]  [{tag}] {message}\n")
    sys.stderr.flush()


def error(tag: str, message: str, exc: Optional[BaseException] = None) -> None:
    """Logs an error message, optionally with exception details."""
    exc_str = f" ({type(exc).__name__}: {exc})" if exc else ""
    sys.stderr.write(f"[{_format_timestamp()}] [ERROR] [{tag}] {message}{exc_str}\n")
    sys.stderr.flush()
