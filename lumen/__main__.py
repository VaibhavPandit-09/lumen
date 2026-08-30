"""
CLI entry point for Lumen command launcher.
"""

from __future__ import annotations

import argparse
import json
import os
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
    from lumen.providers.actions import CustomActionsProvider
    from lumen.providers.applications import ApplicationProvider
    from lumen.providers.calculator import CalculatorProvider
    from lumen.providers.commands import CommandProvider
    from lumen.providers.conversions import ConversionsProvider
    from lumen.providers.currency import CurrencyProvider
    from lumen.providers.krunner import KRunnerProvider
    from lumen.providers.locations import LocationsProvider
    from lumen.providers.packages import PackagesProvider
    from lumen.providers.system_actions import SystemActionsProvider

    config = LumenConfig().load()
    providers = [
        CalculatorProvider(enabled=config.providers.get("calculator", True)),
        ConversionsProvider(enabled=config.providers.get("conversions", True)),
        CurrencyProvider(enabled=config.providers.get("currency", True)),
        CustomActionsProvider(actions_dir=config.actions_dir, enabled=config.providers.get("actions", True)),
        CommandProvider(commands=config.commands, enabled=config.providers.get("commands", True)),
        ApplicationProvider(hidden_applications=config.hidden_applications, enabled=config.providers.get("applications", True)),
        PackagesProvider(enabled=config.providers.get("packages", True)),
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
    try:
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.setApplicationName("lumen")
        QCoreApplication.setOrganizationName("lumen")
        QCoreApplication.setApplicationVersion(__version__)
        QCoreApplication.setOrganizationDomain("github.com/VaibhavPandit-09/lumen")
    except Exception:
        pass

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

    # Actions CLI
    actions_p = subparsers.add_parser("actions", help="Inspect, validate, and run custom actions")
    actions_sub = actions_p.add_subparsers(dest="actions_action", help="Action commands")
    
    act_list_p = actions_sub.add_parser("list", help="List all discovered custom actions")
    act_list_p.add_argument("--json", action="store_true", help="Output actions as JSON")

    act_val_p = actions_sub.add_parser("validate", help="Validate all custom actions on disk")
    act_val_p.add_argument("--json", action="store_true", help="Output validation results as JSON")

    act_info_p = actions_sub.add_parser("info", help="Display details for a specific action")
    act_info_p.add_argument("id", type=str, help="Action ID")
    act_info_p.add_argument("--json", action="store_true", help="Output info as JSON")

    act_run_p = actions_sub.add_parser("run", help="Run a custom action from the CLI")
    act_run_p.add_argument("id", type=str, help="Action ID")
    act_run_p.add_argument("args", nargs="*", help="Optional arguments for the action")

    actions_sub.add_parser("reload", help="Notify running daemon to reload actions from disk")

    # Setup CLI
    setup_p = subparsers.add_parser("setup", help="First-run setup wizard and KDE shortcut configuration")
    setup_p.add_argument("--shortcut", type=str, default="Alt+Space", help="Global shortcut trigger (default: Alt+Space)")
    setup_p.add_argument("--json", action="store_true", help="Output setup status as JSON")

    # Packages CLI
    pkg_p = subparsers.add_parser("packages", help="Unified package management CLI")
    pkg_sub = pkg_p.add_subparsers(dest="pkg_action", help="Package command")

    pkg_search_p = pkg_sub.add_parser("search", help="Search software packages")
    pkg_search_p.add_argument("query", type=str, help="Package search term")
    pkg_search_p.add_argument("--json", action="store_true")

    pkg_inst_p = pkg_sub.add_parser("install", help="Install software package")
    pkg_inst_p.add_argument("package", type=str, help="Package name to install")
    pkg_inst_p.add_argument("--backend", type=str, help="Specific backend (apt, flatpak, snap, pacman)")

    pkg_rm_p = pkg_sub.add_parser("remove", help="Remove/uninstall software package")
    pkg_rm_p.add_argument("package", type=str, help="Package name to remove")
    pkg_rm_p.add_argument("--purge", action="store_true", help="Purge configuration files")
    pkg_rm_p.add_argument("--backend", type=str, help="Specific backend (apt, flatpak, snap, pacman)")

    pkg_up_p = pkg_sub.add_parser("updates", help="Check available software updates")
    pkg_up_p.add_argument("--json", action="store_true")

    # Update CLI
    update_p = subparsers.add_parser("update", help="Update all software packages across active backends")
    update_p.add_argument("--json", action="store_true")

    # Version CLI
    version_p = subparsers.add_parser("version", help="Display version and system build information")
    version_p.add_argument("--json", action="store_true", help="Output version metadata as JSON")

    # Doctor CLI
    doctor_p = subparsers.add_parser("doctor", help="Run system health and integration diagnostic checks")
    doctor_p.add_argument("--json", action="store_true", help="Output diagnostics as JSON")

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
    if args.subcommand == "setup":
        from lumen.service.shortcuts import KDEShortcutManager
        from lumen.core.packages.manager import PackageManager

        is_kde = KDEShortcutManager.is_kde_session()
        shortcut_set, shortcut_msg = False, "Not in KDE session"
        if is_kde:
            shortcut_set, shortcut_msg = KDEShortcutManager.configure_shortcut(shortcut=args.shortcut)

        pkg_mgr = PackageManager.get_instance()
        available_backends = [b.name for b in pkg_mgr.get_available_backends()]

        status_data = {
            "status": "ready" if (is_kde and shortcut_set) or available_backends else "configured",
            "version": __version__,
            "kde_plasma": is_kde,
            "shortcut": args.shortcut,
            "shortcut_configured": shortcut_set,
            "shortcut_message": shortcut_msg,
            "package_backends": available_backends,
        }

        if args.json:
            print(json.dumps(status_data, indent=2))
        else:
            print(f"=== Lumen First-Run Setup (v{__version__}) ===")
            print(f"• Desktop Environment: {'KDE Plasma' if is_kde else 'Other / Standard FreeDesktop'}")
            print(f"• Global Shortcut:      {args.shortcut} ({'✓ Configured' if shortcut_set else shortcut_msg})")
            print("• Package Backends:")
            for b in pkg_mgr.backends.values():
                sym = "✓" if b.is_available() else "—"
                print(f"    {b.name:<10} {sym}")
            print("")
            print(f"Lumen is ready. Press '{args.shortcut}' or run 'lumen toggle' to open.")
            print("==================================================")
        sys.exit(0)

    elif args.subcommand == "packages":
        from lumen.core.packages.manager import PackageManager
        pkg_mgr = PackageManager.get_instance()

        if args.pkg_action == "search":
            results = pkg_mgr.search_all(args.query)
            if args.json:
                print(json.dumps([p.to_dict() for p in results], indent=2))
            else:
                print(f"Software Packages matching '{args.query}':")
                print("=" * 60)
                for p in results:
                    inst = " [installed]" if p.installed else ""
                    print(f"• {p.name} ({p.source_backend.upper()}){inst}")
                    if p.summary:
                        print(f"  {p.summary}")
                print("=" * 60)
            sys.exit(0)

        elif args.pkg_action == "install":
            res = pkg_mgr.install(args.package, backend_id=args.backend)
            print(res.message)
            sys.exit(0 if res.success else 1)

        elif args.pkg_action == "remove":
            res = pkg_mgr.remove(args.package, backend_id=args.backend, purge=args.purge)
            print(res.message)
            sys.exit(0 if res.success else 1)

        elif args.pkg_action == "updates":
            updates = pkg_mgr.check_all_updates()
            if args.json:
                out = {b: [p.to_dict() for p in pkgs] for b, pkgs in updates.items()}
                print(json.dumps(out, indent=2))
            else:
                total = sum(len(pkgs) for pkgs in updates.values())
                print(f"Available Software Updates ({total} total):")
                print("=" * 60)
                for b, pkgs in updates.items():
                    print(f"[{b}] ({len(pkgs)} updates):")
                    for p in pkgs:
                        print(f"  • {p.name} {p.version} -> {p.new_version}")
                print("=" * 60)
            sys.exit(0)

    elif args.subcommand == "update":
        from lumen.core.packages.manager import PackageManager
        pkg_mgr = PackageManager.get_instance()
        results = pkg_mgr.update_all()
        if args.json:
            print(json.dumps({b: r.to_dict() for b, r in results.items()}, indent=2))
        else:
            print("System Software Update Results:")
            print("=" * 60)
            for b, r in results.items():
                status = "✓" if r.success else "❌"
                print(f"• [{b}] {status} {r.message}")
            print("=" * 60)
        sys.exit(0 if all(r.success for r in results.values()) else 1)

    # Handle subcommands
    if args.subcommand == "version":
        cfg = LumenConfig().load()
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        pyqt_ver = "unknown"
        try:
            from PyQt6.QtCore import PYQT_VERSION_STR
            pyqt_ver = PYQT_VERSION_STR
        except Exception:
            pass

        info = {
            "name": "Lumen",
            "tagline": "An agent-friendly command launcher for KDE Plasma",
            "version": __version__,
            "python": py_ver,
            "pyqt6": pyqt_ver,
            "config_version": cfg.config_version,
            "config_dir": str(cfg.resolved_config_dir),
            "actions_dir": str(os.path.expanduser(cfg.actions_dir)),
        }
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"Lumen {__version__} — An agent-friendly command launcher for KDE Plasma")
            print(f"  Python:         {py_ver}")
            print(f"  PyQt6:          {pyqt_ver}")
            print(f"  Config Version: {cfg.config_version}")
            print(f"  Config Dir:     {cfg.resolved_config_dir}")
            print(f"  Actions Dir:    {os.path.expanduser(cfg.actions_dir)}")
        sys.exit(0)

    elif args.subcommand == "doctor":
        from lumen.core.doctor import SystemDoctor
        report = SystemDoctor.run_all_checks()
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(report.format_text())
        sys.exit(0 if report.is_healthy else 1)

    elif args.subcommand == "actions":
        from lumen.core.actions.discovery import ActionScanner
        from lumen.core.actions.executor import ActionContext, ActionExecutor
        from lumen.core.actions.validator import ActionValidator

        cfg = LumenConfig().load()
        scanner = ActionScanner(cfg.actions_dir)
        actions = scanner.scan()

        if args.actions_action == "list":
            if args.json:
                out = [a.to_dict() for a in actions]
                print(json.dumps(out, indent=2))
            else:
                print(f"Discovered Custom Actions ({len(actions)} total in {scanner.get_actions_dir()}):")
                print("=" * 60)
                if not actions:
                    print("No custom actions found. Add manifests to ~/.config/lumen/actions/")
                for a in actions:
                    conf = " [requires confirmation]" if a.confirm else ""
                    print(f"• {a.name} (id: {a.id}){conf}")
                    if a.description:
                        print(f"  {a.description}")
                print("=" * 60)
            sys.exit(0)

        elif args.actions_action == "validate":
            issues = ActionValidator.validate_action_collection(actions)
            if args.json:
                out = [
                    {
                        "severity": i.severity.value,
                        "field": i.field,
                        "message": i.message,
                    }
                    for i in issues
                ]
                print(json.dumps(out, indent=2))
            else:
                print(f"Validating Custom Actions in {scanner.get_actions_dir()}:")
                print("=" * 60)
                if not issues:
                    print("✓ All custom action manifests are valid.")
                else:
                    for i in issues:
                        prefix = "✗ ERROR" if i.severity.value == "error" else "⚠️ WARN "
                        field_info = f" [{i.field}]" if i.field else ""
                        print(f"{prefix}{field_info}: {i.message}")
                print("=" * 60)
            sys.exit(1 if any(i.severity.value == "error" for i in issues) else 0)

        elif args.actions_action == "info":
            found = next((a for a in actions if a.id == args.id), None)
            if not found:
                if args.json:
                    print(json.dumps({"error": f"Action '{args.id}' not found"}, indent=2))
                else:
                    print(f"Error: Action '{args.id}' not found in {scanner.get_actions_dir()}")
                sys.exit(1)

            if args.json:
                print(json.dumps(found.to_dict(), indent=2))
            else:
                print(f"Action: {found.name} ({found.id})")
                print("=" * 60)
                print(f"Description:   {found.description}")
                print(f"Category:      {found.category}")
                print(f"Icon:          {found.icon}")
                print(f"Executable:    {found.exec}")
                print(f"Working Dir:   {found.cwd or 'Default'}")
                print(f"Terminal:      {found.terminal}")
                print(f"Confirmation:  {found.confirm}")
                print(f"Timeout:       {found.timeout_seconds}s")
                print(f"Source Manifest: {found.source_path}")
                if found.args_schema:
                    print("Arguments:")
                    for arg in found.args_schema:
                        req = " (required)" if arg.required else ""
                        print(f"  • {arg.name}{req}: {arg.description}")
                print("=" * 60)
            sys.exit(0)

        elif args.actions_action == "run":
            found = next((a for a in actions if a.id == args.id), None)
            if not found:
                print(f"Error: Action '{args.id}' not found")
                sys.exit(1)
            ctx = ActionContext(action_id=found.id)
            res = ActionExecutor.execute(found, context=ctx)
            if res.stdout:
                print(res.stdout)
            if res.stderr:
                print(res.stderr, file=sys.stderr)
            sys.exit(res.exit_code)

        elif args.actions_action == "reload":
            send_ipc_command("refresh")
            print("Notified running Lumen daemon to reload actions.")
            sys.exit(0)

        else:
            actions_p.print_help()
            sys.exit(0)

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
