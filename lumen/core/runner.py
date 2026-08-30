"""
Safe process execution engine for applications, shell commands, URLs, and terminal tasks.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from typing import Dict, List, Optional


def find_terminal_emulator() -> Optional[str]:
    """Finds the first available terminal emulator installed on the system."""
    terminals = [
        "ghostty",
        "konsole",
        "alacritty",
        "kitty",
        "wezterm",
        "foot",
        "gnome-terminal",
        "xfce4-terminal",
        "xterm",
    ]
    for term in terminals:
        path = shutil.which(term)
        if path:
            return path
    return None


def clean_desktop_exec(exec_cmd: str) -> List[str]:
    """
    Cleans FreeDesktop Exec field codes (%f, %F, %u, %U, etc.) and returns argv list.
    """
    # Remove field codes
    cleaned = re.sub(r"%[fFuUdDnNickvm]", "", exec_cmd).strip()
    try:
        args = shlex.split(cleaned)
    except Exception:
        args = cleaned.split()
    return args


def launch_desktop_file(
    exec_cmd: str,
    terminal: bool = False,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> bool:
    """Launches an application defined by a .desktop file Exec line."""
    args = clean_desktop_exec(exec_cmd)
    if not args:
        return False

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    target_cwd = cwd if (cwd and os.path.isdir(cwd)) else None

    if terminal:
        term = find_terminal_emulator()
        if term:
            if "konsole" in term:
                args = [term, "-e"] + args
            elif "gnome-terminal" in term:
                args = [term, "--"] + args
            else:
                args = [term, "-e"] + args
        else:
            # Fallback without terminal if none found
            pass

    try:
        subprocess.Popen(
            args,
            cwd=target_cwd,
            env=full_env,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True
    except Exception:
        return False


def launch_shell_command(
    command: str,
    terminal: bool = False,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> bool:
    """Executes a user command string safely in background or terminal."""
    if not command.strip():
        return False

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    target_cwd = cwd if (cwd and os.path.isdir(cwd)) else os.path.expanduser("~")

    try:
        if terminal:
            term = find_terminal_emulator()
            if term:
                if "konsole" in term:
                    cmd_args = [term, "-e", "bash", "-c", f"{command}; echo ''; read -p 'Press Enter to close...'"]
                elif "gnome-terminal" in term:
                    cmd_args = [term, "--", "bash", "-c", f"{command}; echo ''; read -p 'Press Enter to close...'"]
                else:
                    cmd_args = [term, "-e", "bash", "-c", f"{command}; echo ''; read -p 'Press Enter to close...'"]
                subprocess.Popen(
                    cmd_args,
                    cwd=target_cwd,
                    env=full_env,
                    start_new_session=True,
                    close_fds=True,
                )
                return True

        # Run non-terminal command detached
        subprocess.Popen(
            ["/bin/bash", "-c", command],
            cwd=target_cwd,
            env=full_env,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True
    except Exception:
        return False


def open_path_or_url(target: str) -> bool:
    """Opens a local file, folder, or web URL with the default handler (xdg-open / kde-open6)."""
    if not target:
        return False

    openers = ["kde-open6", "kde-open5", "gio", "xdg-open"]
    for opener in openers:
        if shutil.which(opener):
            try:
                cmd = [opener, "open", target] if opener == "gio" else [opener, target]
                subprocess.Popen(
                    cmd,
                    start_new_session=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
                return True
            except Exception:
                continue

    # Fallback to webbrowser module if URL
    if target.startswith(("http://", "https://")):
        import webbrowser
        try:
            webbrowser.open(target)
            return True
        except Exception:
            return False

    return False
