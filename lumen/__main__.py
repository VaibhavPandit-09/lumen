"""
CLI entry point for Lumen command launcher.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lumen import __version__
from lumen.core.config import LumenConfig
from lumen.core.logging import debug, is_debug, set_debug
from lumen.core.models import CommandItem
from lumen.service.daemon import LumenAppDaemon, send_ipc_command
from lumen.service.shortcuts import get_shortcut_setup_instructions


def cli_search(query: str, as_json: bool = False) -> None:
    """Executes a search via CLI without launching GUI."""
    from lumen.providers.applications import ApplicationProvider
    from lumen.providers.calculator import CalculatorProvider
    from lumen.providers.commands import CommandProvider
    from lumen.providers.krunner import KRunnerProvider
    from lumen.providers.locations import LocationsProvider
    from lumen.providers.system_actions import SystemActionsProvider

    config = LumenConfig().load()
    providers = [
        CalculatorProvider(enabled=config.providers.get("calculator", True)),
        CommandProvider(commands=config.commands, enabled=config.providers.get("commands", True)),
        ApplicationProvider(hidden_applications=config.hidden_applications, enabled=config.providers.get("applications", True)),
        SystemActionsProvider(enabled=config.providers.get("system_actions", True)),
        LocationsProvider(enabled=config.providers.get("locations", True)),
        KRunnerProvider(enabled=config.providers.get("krunner", True)),
    ]

    for p in providers:
        p.initialize()

    results = []
    for p in providers:
        if p.enabled:
            results.extend(p.safe_search(query))

    results.sort(key=lambda x: x.score, reverse=True)
    top_results = results[: config.max_results]

    if as_json:
        out = [
            {
                "id": r.id,
                "title": r.title,
                "subtitle": r.subtitle,
                "category": r.category,
                "badge": r.badge,
                "score": r.score,
                "origin_provider": r.origin_provider,
            }
            for r in top_results
        ]
        print(json.dumps(out, indent=2))
    else:
        print(f"Lumen Search Results for: '{query}'")
        print("=" * 60)
        if not top_results:
            print("No matching local results.")
        for idx, r in enumerate(top_results, 1):
            badge = f" [{r.badge}]" if r.badge else ""
            print(f"{idx}. {r.title}{badge}")
            if r.subtitle:
                print(f"   {r.subtitle}")
        print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lumen",
        description="Lumen — an agent-friendly command launcher for KDE Plasma",
    )
    parser.add_argument("-v", "--version", action="version", version=f"Lumen {__version__}")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable verbose debug logging")

    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommands")

    # Toggle / launch
    subparsers.add_parser("toggle", help="Toggle launcher window visibility (used for hotkeys)")
    subparsers.add_parser("show", help="Show launcher window")
    subparsers.add_parser("hide", help="Hide launcher window")
    subparsers.add_parser("daemon", help="Run Lumen in background daemon mode")
    subparsers.add_parser("shortcut", help="Display KDE global shortcut configuration instructions")

    # Search CLI
    search_p = subparsers.add_parser("search", help="Execute search directly via CLI")
    search_p.add_argument("query", type=str, help="Search query string")
    search_p.add_argument("--json", action="store_true", help="Output results as JSON")

    # Config CLI
    config_p = subparsers.add_parser("config", help="Manage Lumen configuration")
    config_p.add_argument("action", choices=["path", "show", "edit", "add-command"], help="Config action")
    config_p.add_argument("--name", type=str, help="Command name (for add-command)")
    config_p.add_argument("--cmd", type=str, help="Shell command (for add-command)")
    config_p.add_argument("--desc", type=str, default="", help="Description (for add-command)")
    config_p.add_argument("--category", type=str, default="Commands", help="Category (for add-command)")
    config_p.add_argument("--terminal", action="store_true", help="Run in terminal (for add-command)")

    args = parser.parse_args()

    if args.debug:
        set_debug(True)
        debug("CLI", "Verbose debug logging enabled.")

    # Handle subcommands
    if args.subcommand == "toggle":
        if not send_ipc_command("toggle"):
            # Start new instance and show
            daemon = LumenAppDaemon()
            sys.exit(daemon.start(show_immediately=True))
        sys.exit(0)

    elif args.subcommand == "show":
        if not send_ipc_command("show"):
            daemon = LumenAppDaemon()
            sys.exit(daemon.start(show_immediately=True))
        sys.exit(0)

    elif args.subcommand == "hide":
        send_ipc_command("hide")
        sys.exit(0)

    elif args.subcommand == "daemon":
        if send_ipc_command("show"):
            print("Lumen daemon is already running.")
            sys.exit(0)
        daemon = LumenAppDaemon()
        sys.exit(daemon.start(show_immediately=False))

    elif args.subcommand == "shortcut":
        config = LumenConfig().load()
        print(get_shortcut_setup_instructions(config.shortcut))
        sys.exit(0)

    elif args.subcommand == "search":
        cli_search(args.query, as_json=args.json)
        sys.exit(0)

    elif args.subcommand == "config":
        cfg = LumenConfig().load()
        if args.action == "path":
            print(f"Config directory: {cfg.config_dir}")
            print(f"Main config:     {cfg.config_file}")
            print(f"Commands config: {cfg.commands_file}")
        elif args.action == "show":
            print(f"=== {cfg.config_file} ===")
            print(cfg.config_file.read_text(encoding="utf-8") if cfg.config_file.exists() else "Not created yet")
            print(f"\n=== {cfg.commands_file} ===")
            print(cfg.commands_file.read_text(encoding="utf-8") if cfg.commands_file.exists() else "Not created yet")
        elif args.action == "edit":
            from lumen.core.runner import open_path_or_url
            open_path_or_url(str(cfg.commands_file))
        elif args.action == "add-command":
            if not args.name or not args.cmd:
                print("Error: --name and --cmd are required to add a command.")
                sys.exit(1)
            new_cmd = CommandItem(
                name=args.name,
                command=args.cmd,
                description=args.desc,
                category=args.category,
                terminal=args.terminal,
            )
            cfg.add_command(new_cmd)
            # Notify running daemon if active
            send_ipc_command("refresh")
            print(f"Successfully added command '{args.name}' to {cfg.commands_file}")
        sys.exit(0)

    # Default action with no arguments: toggle or start
    if not send_ipc_command("toggle"):
        daemon = LumenAppDaemon()
        sys.exit(daemon.start(show_immediately=True))
    sys.exit(0)


if __name__ == "__main__":
    main()
