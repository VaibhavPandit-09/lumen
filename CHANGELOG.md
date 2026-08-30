# Changelog

All notable changes to **Lumen** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
