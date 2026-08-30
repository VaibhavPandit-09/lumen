# Changelog

All notable changes to **Lumen** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-08-30

### Added
- **Hierarchical Category Navigation (`NavigationManager`)**: Structured surfaces for **Apps**, **Packages**, **Updates**, **Commands**, **Files**, and **System** with progressive disclosure, dynamic placeholder text, and predictive breadcrumb paths.
- **Universal Escape Hierarchy**: Resolved Escape preemption bug; Escape key now strictly unwinds one layer at a time: cancels pending confirmation -> pops submenus -> pops category surfaces -> clears search text -> dismisses overlay.
- **Software Entity Model (`SoftwareItem`)**: Rich software metadata model with `SoftwareKind` (Application, Package, Runtime, Library, CLI), capabilities mapping, and source tracking across backends.
- **One-Click GitHub Release Self-Updating (`SelfUpdater`, `UpdateChecker`)**: Background update checker with caching, backoff, and offline tolerance; automated release discovery via GitHub API; SHA-256 checksum verification; staged tarball extraction; atomic directory replacement; and automatic rollback upon verification failure (`lumen update --self` / `lumen update --check`).
- **Dedicated Updates Surface & Provider (`UpdatesProvider`)**: Unified update dashboard displaying pending Lumen releases and system package updates per backend with one-click "Update All".
- **Cross-Thread UI Safety**: Signal-based callback marshalling via `_progress_signal` and `_complete_signal` ensuring all UI widget mutations strictly execute on the Qt main GUI thread.
- **Package Manager Hardening**: Non-blocking async search and update query APIs (`search_all_async`, `check_all_updates_async`), input regex validation for Flatpak and Snap backends, and false-success detection on failed transaction outcomes.
- **Expanded System Health Diagnostics (`lumen doctor`)**: Added validation checks for installation method detection, self-update capability, GitHub API connectivity with latency measurement, and Lumen update cache status.
- **Comprehensive Automated Test Suite**: Expanded test suite to **163 automated tests** (100% pass rate) across 37 test modules.

## [0.5.0] - 2026-08-30

### Added
- **Desktop-Grade Launcher Interaction Contract**: Established canonical `ActionDispatcher` ensuring identical execution for keyboard (`Enter`) and mouse clicks; added `FocusPolicy.NoFocus` to result lists guaranteeing keyboard focus always stays in the search bar; instant `Escape` dismissal.
- **Universal Software Management Platform**: Unified software abstraction (`BasePackageBackend`, `PackageManager`) supporting **APT**, **Flatpak**, **Snap**, and **Pacman** with PolicyKit (`pkexec`) privilege elevation and concurrency locking.
- **Natural Command Intent Parsing**: Direct support for typing natural intents (`install <pkg>`, `uninstall <pkg>`, `update <pkg>`, `update all`, `updates`).
- **First-Class KDE Global Shortcut Setup (`lumen setup`)**: Automated setup wizard detecting KDE Plasma 6/5 and registering `Alt+Space` via native KDE tools (`kwriteconfig6`, `qdbus6`, `kglobalshortcutsrc`).
- **Expanded CLI Software Management**: Added `lumen setup`, `lumen packages [search|install|remove|updates]`, and `lumen update` subcommands with machine-readable `--json` modes.
- **Immediate Application Re-Indexing**: Newly installed/removed applications automatically trigger background desktop file scanning for instant searchability without rebooting.
- **Expanded Test Suite**: Comprehensive test suite with 112 automated tests (100% pass rate in headless mode).

## [0.4.0] - 2026-08-30

### Added
- **Health & Diagnostic Subsystem (`lumen doctor`)**: Integrated diagnostic engine (`SystemDoctor`) executing 12 validation checks across runtime, Qt bindings, desktop sessions, PATH, executable integrity, desktop entries, icons, configs, actions, and IPC with human-readable and `--json` machine-readable output.
- **Configuration Migrations & Automatic Backups**: `ConfigMigrator` framework with schema versioning (`config_version: 1`), automated timestamped backup creation (`config.jsonc.backup-YYYYMMDD-HHMMSS`), retention pruning (keeping newest 5 backups), and safe downgrade warnings.
- **Single Source of Truth Versioning**: Authoritative version definition in `pyproject.toml` and `lumen/__init__.py`, synchronized across `PKGBUILD`, `debian/changelog`, and `lumen version [--json]`.
- **Production User-Local Lifecycle Installer**: Rewritten `install.sh` supporting `--check`, `--version`, preflight dependency validation, daemon termination during upgrade, custom action and configuration preservation, and tailored shell PATH instructions (bash, zsh, fish).
- **Safe Uninstaller & Purge**: Rewritten `uninstall.sh` supporting `--check`, normal uninstallation (preserves user configuration and actions in `~/.config/lumen`), and `--purge` with interactive confirmation.
- **Automated Release Packaging Pipeline**: Added `.github/workflows/release.yml` for building source distribution artifacts, Debian packages (`.deb`), and generating `SHA256SUMS` checksums on version tags.
- **Dedicated Upgrading & Lifecycle Documentation**: Added `docs/UPGRADING.md` covering upgrade safety guarantees, rollback procedures, and uninstallation.
- **Expanded Test Suite**: Expanded test coverage to 81 automated tests (100% pass rate).

## [0.3.0] - 2026-08-30

### Added
- **Custom Action Scripting Engine**: Extensible custom action runtime supporting declarative `.jsonc` manifests in `~/.config/lumen/actions/` (`ActionDefinition`, `ActionScanner`, `ActionExecutor`, `ActionValidator`).
- **Confirmation Safety Guard**: Dangerous actions can declare `"confirm": true` with custom confirmation prompts, prompting the user with an interactive confirmation state before execution.
- **Physical, Time & Data Unit Conversions**: Fast deterministic conversions across length, mass, temperature, speed, area, volume, data size, and time (`ConversionsProvider` & `lumen.core.units`).
- **Cached Currency Conversions**: Offline-capable currency rate conversions (`CurrencyProvider` & `currency_rates.json`).
- **Advanced Mathematical Capabilities**: Safe AST math parser expanded with `gcd`, `lcm`, `hypot`, `atan2`, `factorial`, and angle expressions (`sin(45 deg)`).
- **Optional KDE Plasma System Tray Companion**: `LumenTrayCompanion` leveraging `QSystemTrayIcon` with status, toggle, reload, and quit actions.
- **Custom Action CLI Suite**: `lumen actions list [--json]`, `lumen actions validate [--json]`, `lumen actions info <id> [--json]`, `lumen actions run <id>`, `lumen actions reload`.
- **Comprehensive Extension Documentation**: Added dedicated `docs/EXTENSION_API.md` and working starter examples in `examples/custom_actions/`.
- **Expanded Automated Tests**: Expanded test suite to 67 automated tests with 100% headless pass rate.

## [0.2.0] - 2026-08-30

### Added
- **Subtle Transitions & Animations**: Non-blocking fluid entry and dismissal transitions (`WindowAnimationManager`) with configurable duration (120ms).
- **Optional KRunner Provider**: D-Bus adapter querying KDE Plasma 6 KRunner runners when available with graceful fallback.
- **Custom Application Icon**: Polished vector SVG icon asset installed to standard FreeDesktop icon directories.
- **Debian & Arch Packaging**: Full Debian package recipes (`debian/control`, `debian/rules`, `debian/changelog`) and Arch Linux `PKGBUILD`.
- **Diagnostic Logging Subsystem**: Integrated `--debug` / `-d` CLI flag and `lumen.core.logging` with strict user privacy safeguards.
- **Expanded Test Suite**: Automated coverage expanded from 30 to 47 tests across animations, KRunner adapter, IPC recovery, keyboard interaction, and error boundaries.

### Improved
- **Multi-Monitor Cursor Centering**: Dynamic positioning on active monitor based on cursor location (`QGuiApplication.screenAt(QCursor.pos())`).
- **Single-Instance IPC Hardening**: Stale socket detection, user permission isolation (`0o700`), and OS signal handlers (`SIGINT`, `SIGTERM`).
- **App Scanner Performance**: mtime-based parsing cache and prioritized deduplication favoring user-local desktop entries.
- **Keyboard Interaction**: Full support for `Shift+Tab`, `Left`, `Right`, `Home`, `End`, and accessible screen reader descriptions.
- **Empty State UX**: Clean empty state row with direct browser web search fallback action when local results yield no matches.
- **Error Boundary Isolation**: Safe search execution isolating provider exceptions without crashing the UI or search pipeline.

## [0.1.0] - 2026-08-30

### Initial Release
- **Core Architecture**:
  - Native PyQt6 / Qt 6.10 application for KDE Plasma 6.
  - Multi-tier fuzzy search engine with acronym and prefix bonuses.
  - XDG `.desktop` file parser with live `QFileSystemWatcher` file monitoring.
  - Safe runner for detached background processes and terminal commands.
- **Providers**:
  - Applications Provider (system, user, Flatpak, and Snap `.desktop` entries).
  - User Commands Provider (JSONC-configured commands, categories, and nested submenus).
  - KDE System Actions Provider (Lock, Logout, Suspend, Restart, Shutdown, System Settings).
  - Common Locations Provider (Home, Documents, Downloads, Music, Pictures, Videos, Desktop).
  - Instant Calculator Provider (safe AST math evaluator with percentages, trig, powers, roots).
  - KDE Recent Files Provider (`~/.local/share/recently-used.xbel` parser).
  - KDE Clipboard Provider.
  - Fallback Web Search Provider.
- **UI / UX**:
  - Modern centered floating command palette overlay with smooth keyboard navigation.
  - Submenu drill-down (`Tab` / `Right`) and back navigation (`Backspace`).
  - Adaptive KDE Breeze dark/light theme integration.
  - Dynamic result badges, high-DPI icons, and category headers.
- **Agent Malleability**:
  - JSONC configuration in `~/.config/lumen/config.jsonc` and `~/.config/lumen/commands.jsonc`.
  - JSON Schema (`schema.json`) for validation and IDE completions.
  - Comprehensive AI agent documentation and extension examples.
- **Tooling & CI**:
  - GitHub Actions CI workflow with headless offscreen test automation.
  - Local installation and uninstallation scripts (`install.sh`, `uninstall.sh`).
  - Single-instance D-Bus / socket daemon for instant shortcut toggling.
