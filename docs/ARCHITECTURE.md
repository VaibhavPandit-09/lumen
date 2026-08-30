# Lumen Architecture Blueprint

Lumen is an agent-friendly command launcher and command palette built natively for **KDE Plasma**. It provides an instantaneous, keyboard-driven surface for launching applications, running nested custom commands, triggering system actions, calculating mathematical formulas, navigating folders, and executing AI-agent-created workflows.

```
+-------------------------------------------------------------------------+
|                              Lumen UI                                   |
|   +-----------------------------------------------------------------+   |
|   |  Breadcrumb / Submenu: Lumen > Development                      |   |
|   |  SearchBar: [ Type a command or math...                      ]  |   |
|   |  ResultListWidget:                                              |   |
|   |   +-----------------------------------------------------------+ |   |
|   |   | [Icon] Title              Subtitle/Path          [Badge]  | |   |
|   |   +-----------------------------------------------------------+ |   |
|   |  Footer: (↑↓ Navigate • ↵ Launch • Tab Submenu • Esc Dismiss)   |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
                                    |
                    +---------------+---------------+
                    |                               |
          [ LauncherWindow ]               [ Single-Instance IPC ]
                    |                       (QLocalServer / Socket)
                    v                               ^
          [ Providers Manager ]                     |
     +--------------+--------------+         [ lumen toggle / CLI ]
     |              |              |
     v              v              v
[ Applications ] [ Commands ] [ System Actions ]
[ Calculator   ] [ Locations] [ Recent Files   ]
[ Clipboard    ] [ Web Search] [ KRunner (opt) ]
     |              |              |
     +--------------+--------------+
                    |
                    v
            [ Core Engine ]
    - Fuzzy & Acronym Matcher (fuzzy.py)
    - XDG App Scanner & Watcher (app_scanner.py)
    - Safe Process Runner (runner.py)
    - Safe AST Calculator (calculator.py)
    - JSONC Config Engine (config.py & schema.json)
    - Privacy Logging Subsystem (logging.py)
    - Window Animation Manager (animations.py)
```

---

## 1. Chosen UI Technology

* **Framework**: **PyQt6 (Qt 6.10+)** leveraging `QtWidgets` and native Qt 6 window management.
* **Window Properties**:
  * `Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint`
  * `Qt.WidgetAttribute.WA_TranslucentBackground`
* **Animations**: Native Qt property animations (`QPropertyAnimation` over `windowOpacity`) running non-blocking 120ms transitions.
* **Rendering**: High-performance custom item painting via `QStyledItemDelegate` (`ResultItemDelegate`), avoiding heavy widget overhead and allowing instantaneous 60+ FPS keyboard scrolling.
* **Theme Integration**: Automatic detection of KDE Breeze dark/light palette with real-time luminance checking, custom vector icon assets, and crisp typography.

---

## 2. Application Indexing Approach

* **Discovery**: Scans standard FreeDesktop XDG directories:
  * `~/.local/share/applications`
  * `/usr/local/share/applications`
  * `/usr/share/applications`
  * `/var/lib/flatpak/exports/share/applications` and user Flatpak exports
  * `/var/lib/snapd/desktop/applications`
* **Parsing**: Fast INI parser extracting `Name`, `GenericName`, `Comment`, `Exec`, `Icon`, `Categories`, `Keywords`, `Terminal`, `NoDisplay`, `OnlyShowIn`, and Desktop Actions (`[Desktop Action ...]`).
* **Live Invalidation**: Monitors application folders using `QFileSystemWatcher`. New applications or uninstalled packages automatically update the search index without requiring manual database rebuilds.
* **User App Hiding**: Supports hiding specific applications by `.desktop` filename or name via `config.jsonc` without altering system files.

---

## 3. Fuzzy-Search & Acronym Implementation

Search matching is handled in `lumen.core.fuzzy` via a multi-tiered scoring pipeline:
1. **Exact Match**: 1000 base score + case match bonus.
2. **Exact Prefix Match**: 800 base score + length density ratio.
3. **Word-Boundary Match**: 650 base score for matches starting at word separators (` `, `-`, `_`, `.`, `/`).
4. **Acronym Matching**: 600 base score for matches against the first letters of words and camelCase transitions (e.g. `gc` -> `Google Chrome`, `ksp` -> `KSystemLog`, `vsc` -> `Visual Studio Code`).
5. **Subsequence Matching**: Character-by-character scan with consecutive-match multipliers (+12 per consecutive char), start-of-string bonus (+25), word boundary bonuses (+20), and gap/span distance penalties.
6. **Composite Item Scoring**: Combines Title (1.0 weight), Keywords (0.8 weight), Subtitle (0.5 weight), and Category (0.3 weight).

---

## 4. Command Configuration Format

Lumen utilizes **JSONC** (JSON with comments) for configuration:
* `~/.config/lumen/config.jsonc`: General preferences (window dimensions, providers, opacity, hidden applications).
* `~/.config/lumen/commands.jsonc`: User and AI-agent created custom commands, nested submenus, and workflows.

### Why JSONC?
* **Human-Readable & Commentable**: Allows developers and agents to explain why a command was added.
* **Schema-Validated**: Governed by `lumen/core/schema.json` with IDE validation and auto-completions.
* **Zero Opaque State**: No proprietary SQLite binary caches or hidden state.

---

## 5. Global Shortcut Mechanism

* **Default Shortcut**: `Meta+Space` (Super+Space).
* **Execution Pathway**:
  1. KDE Plasma executes `lumen toggle`.
  2. The lightweight CLI client connects to the running daemon via local domain socket (`/tmp/lumen_ipc_<uid>.sock`) and sends `"toggle\n"`.
  3. The daemon receives the signal in < 3ms and instantly raises/toggles the launcher overlay.
  4. If the daemon is not running, it initializes immediately.
* **Conflict Mitigation**: Documented in `lumen shortcut` and configured via standard KDE System Settings Shortcuts KCM.

---

## 6. KDE Plasma Integration Mechanisms

* **System Power & Sessions**:
  * Lock: `org.freedesktop.ScreenSaver /ScreenSaver Lock` / `loginctl lock-session`
  * Logout: `org.kde.Shutdown /Shutdown logout` / `org.kde.ksmserver`
  * Suspend: `org.freedesktop.login1 /org/freedesktop/login1 Suspend` / `systemctl suspend`
  * Reboot / Shutdown: `org.kde.Shutdown /Shutdown logoutAndReboot` / `logoutAndShutdown`
  * Settings: `systemsettings <kcm_module>` / `kcmshell6`
* **Locations**: Standard XDG user directories resolved via `pathlib` and opened with `xdg-open` / `kde-open6`.
* **Recent Files**: FreeDesktop standard XML `~/.local/share/recently-used.xbel`.
* **Clipboard**: Qt `QApplication.clipboard()` without running a competing background daemon.

---

## 7. Process & Lifecycle Model

* **Single-Instance Daemon**: When launched, Lumen listens on a Unix domain socket in `XDG_RUNTIME_DIR`.
* **Instant Activation**: Calling `lumen toggle` does not restart Python or re-import modules; it delivers a socket packet to the running instance, yielding sub-15ms response times.
* **Auto-Dismiss**: When the user clicks outside or the window loses focus, Lumen dismisses gracefully.
* **Detached Execution**: Applications and shell commands are launched using `subprocess.Popen` with `start_new_session=True`, ensuring child processes survive independently of the launcher.

---

## 8. Testing Strategy

* **Headless Execution**: All tests run headlessly in CI and local machines using `QT_QPA_PLATFORM=offscreen`.
* **Automated Suites**:
  * `test_fuzzy.py`: Fuzzy matching, acronyms, word boundaries, weighting.
  * `test_app_scanner.py`: `.desktop` parsing, exec sanitization, hidden apps filtering.
  * `test_calculator.py`: Safe math evaluation, percentages, safety sandboxing.
  * `test_config.py`: JSONC parsing, comments, schema serialization.
  * `test_commands.py`: Nested command trees and search queries.
  * `test_providers.py`: Provider initialization and result scoring.
  * `test_ui_headless.py`: Launcher window instantiation, event handling, navigation stack.
