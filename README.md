# Lumen — an agent-friendly command launcher for KDE Plasma

[![CI](https://github.com/VaibhavPandit-09/lumen/actions/workflows/ci.yml/badge.svg)](https://github.com/VaibhavPandit-09/lumen/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![KDE Plasma 6](https://img.shields.io/badge/KDE%20Plasma-6-blue.svg)](https://kde.org/plasma-desktop/)
[![Qt 6](https://img.shields.io/badge/Qt-6.10-green.svg)](https://www.qt.io/)
[![Python 3](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/tests-112%20passed-brightgreen.svg)](https://github.com/VaibhavPandit-09/lumen/actions)

**Lumen** is a fast, malleable command launcher, command palette, and universal software management surface designed natively for **KDE Plasma**.

It acts as a unified command surface for your desktop—letting you launch applications, install/update packages across package managers, run nested system and developer commands, navigate files, calculate mathematical expressions, and trigger custom workflows with instant keyboard-driven feedback.

---

## 💡 Philosophy & Origin

Lumen is inspired by the swift, keyboard-first launcher and menu experience of **Omarchy Quattro**.

However, Lumen is an **independent, standalone KDE application** built with the following core principles:
* **Conventional Floating Desktop**: Maintains KDE Plasma's standard floating-window workflow. It does **not** enforce or reproduce tiling-window-manager mechanics.
* **No External Distro/Shell Dependencies**: Does **not** require Arch Linux, Omarchy, Hyprland, Quickshell, or any Omarchy-specific packages or configurations.
* **Desktop-Grade Command Surface**: Operates as a true desktop overlay—appearing on `Alt+Space`, instantly accepting focus, executing via `Enter` or mouse click, and immediately dismissing without cluttering the taskbar.
* **Universal Software Management**: Seamlessly searches, installs, updates, and removes packages across **APT**, **Flatpak**, **Snap**, and **Pacman** without needing to remember individual CLI syntax.
* **Agent-First Malleability**: Designed from the ground up so that **AI coding agents** (and power users) can inspect the codebase, understand human-readable JSONC configurations, and seamlessly extend launcher commands, menus, and automation without touching opaque binary databases.
* **Native KDE & Qt 6 Integration**: Built directly with Qt 6 and KDE Plasma D-Bus APIs, respecting system themes, high-DPI scaling, and Wayland/X11 sessions.

> **Disclaimer:** Lumen is an independent open-source project. It is not affiliated with, sponsored by, or endorsed by Omarchy, Basecamp, or 37signals.

---

## ✨ Features

* 🚀 **Instant Application Launching**: Discovers `.desktop` applications from system, user, Flatpak, and Snap directories with live filesystem watching (`QFileSystemWatcher`) and intelligent deduplication.
* 📦 **Universal Software Management**: Unified software discovery and package operations for **APT**, **Flatpak**, **Snap**, and **Pacman** with PolicyKit (`pkexec`) elevation.
* ⚡ **Natural Command Intents**: Type `install vscode`, `uninstall docker`, `update htop`, or `update all` directly in the search bar.
* 🛠️ **Custom Action Scripting Engine**: Create powerful standalone actions and workflows in `~/.config/lumen/actions/` using declarative `.jsonc` manifests with safe execution, argument substitution, and timeouts.
* ⚠️ **Destructive Action Confirmation**: Dangerous actions declare `"confirm": true` to require an explicit interactive confirmation step before execution.
* 🎯 **Intelligent Fuzzy & Acronym Matching**: Multi-tier subsequence matching with word-boundary bonuses and acronym recognition (e.g. `ksp` for `KSystemLog`, `ff` for `Firefox`, `gc` for `Google Chrome`).
* 🌲 **Nested Command Groups & Submenus**: Group commands logically (`Development`, `Docker`, `Git`, `System`) with interactive drill-down (`Tab` / `Right`) or direct unified search.
* ⚡ **KDE System Actions**: Built-in actions for Lock, Logout, Suspend, Restart, Shutdown, and instant access to KDE System Settings panels.
* 🧩 **Optional KRunner Interoperability**: Optional D-Bus adapter querying KDE Plasma 6 KRunner runners when available, with graceful degradation.
* 🧮 **Advanced Safe Calculator**: Arithmetic, trigonometry (`sin(45 deg)`), powers, roots, factorials, GCD, and LCM with safe AST sandboxing.
* 📐 **Physical & Data Unit Conversions**: Instant deterministic conversion for length, mass, temperature, speed, area, volume, data size, and time (e.g. `100 km in miles`, `72 F in C`, `50 km/h in mph`, `2 GB in MB`).
* 💱 **Cached Currency Conversions**: Offline-capable currency conversions (e.g. `100 USD in EUR`, `50 GBP to JPY`, `$100 to EUR`).
* 📁 **Common Locations & Recent Files**: Rapid navigation to standard folders (Home, Downloads, Documents, etc.) and recently used documents (`recently-used.xbel`).
* 📋 **Clipboard Search**: Integrates directly with KDE clipboard history without spawning competing daemons.
* 🌐 **Fallback Web Search**: Intelligently falls back to searching your query in your configured default browser.
* 🗔 **Optional System Tray Companion**: Clean companion tray icon for toggling, reloading, and status.
* ✨ **Subtle 120ms Transitions**: Non-blocking fluid entry and dismissal animations.
* 🎨 **Breeze & Adaptive Theme**: Seamlessly adapts to KDE dark and light color schemes with custom SVG icon assets.
* 🤖 **AI-Agent Ready**: Comprehensive CLI inspection (`lumen doctor --json`, `lumen packages search <query> --json`, `lumen version --json`) and clean JSON schema validation.

---

## ⌨️ Keyboard & Mouse Contract

| Action | Input |
|---|---|
| **Toggle Launcher** | `Alt + Space` (or `lumen toggle`) |
| **Navigate Results** | `Up` / `Down` (or `PageUp` / `PageDown`) |
| **Execute Selected Item** | `Enter` (or `Return`) |
| **Mouse Execute** | Click any item |
| **Open Submenu / Drill Down** | `Tab` / `Right Arrow` |
| **Go Back / Pop Level** | `Shift + Tab` / `Backspace` (on empty text) |
| **Dismiss / Close Overlay** | `Escape` |

---

## 📦 Installation & Zero-Friction Setup

### Prerequisites
* **KDE Plasma 6** (or Plasma 5.27+)
* **Python 3.10+** with **PyQt6** (`python3-pyqt6` on Debian/Ubuntu/Kubuntu)
* `git`

### One-Command Quick Install
```bash
# Clone the repository
git clone https://github.com/VaibhavPandit-09/lumen.git
cd lumen

# Run installer (automatically checks prerequisites and configures Alt+Space)
./install.sh
```

### First-Run Setup & Diagnostics
```bash
# Run first-run setup wizard
lumen setup

# Run system health diagnostics
lumen doctor
```

---

## 🚀 Universal Software Management Examples

Type directly into the Lumen search bar:

```text
firefox          → Launch installed Firefox OR install via Flatpak/APT
install vscode   → Install VS Code via available package manager
uninstall htop   → Safely remove htop (prompts for confirmation)
update all       → Check and apply updates across APT, Flatpak, Snap, and Pacman
```

CLI Software Management:
```bash
# Search packages across all active backends
lumen packages search neovim

# View available software updates
lumen packages updates

# Update all packages
lumen update
```

---

## 🛠️ Configuration & Custom Commands

Lumen stores its configuration in human-readable JSONC (JSON with comments) under `~/.config/lumen/`:
* `~/.config/lumen/config.jsonc` — General preferences (shortcut, theme, window size, opacity, providers).
* `~/.config/lumen/commands.jsonc` — Custom commands and nested menus.
* `~/.config/lumen/actions/` — Standalone declarative custom action manifests (`.jsonc`).

---

## 🧪 Testing

Lumen has a 100% automated test suite with **112+ tests** covering unit logic, error isolation, custom actions, conversions, package backends, and headless Qt UI interactions:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📄 License

Lumen is open-source software licensed under the [MIT License](LICENSE).
