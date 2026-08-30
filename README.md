# Lumen — an agent-friendly command launcher for KDE Plasma

[![CI](https://github.com/VaibhavPandit-09/lumen/actions/workflows/ci.yml/badge.svg)](https://github.com/VaibhavPandit-09/lumen/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![KDE Plasma 6](https://img.shields.io/badge/KDE%20Plasma-6-blue.svg)](https://kde.org/plasma-desktop/)
[![Qt 6](https://img.shields.io/badge/Qt-6.10-green.svg)](https://www.qt.io/)
[![Python 3](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)

**Lumen** is a fast, malleable command launcher and command palette designed natively for **KDE Plasma**.

It acts as a unified command surface for your desktop—letting you launch applications, run nested system and developer commands, navigate files, calculate mathematical expressions, search clipboard history, and trigger custom workflows with instant keyboard-driven feedback.

---

## 💡 Philosophy & Origin

Lumen is inspired by the swift, keyboard-first launcher and menu experience of **Omarchy Quattro**.

However, Lumen is an **independent, standalone KDE application** built with the following core principles:
* **Conventional Floating Desktop**: Maintains KDE Plasma's standard floating-window workflow. It does **not** enforce or reproduce tiling-window-manager mechanics.
* **No External Distro/Shell Dependencies**: Does **not** require Arch Linux, Omarchy, Hyprland, Quickshell, or any Omarchy-specific packages or configurations.
* **Agent-First Malleability**: Designed from the ground up so that **AI coding agents** (and power users) can inspect the codebase, understand human-readable JSONC configurations, and seamlessly extend launcher commands, menus, and automation without touching opaque binary databases.
* **Native KDE & Qt 6 Integration**: Built directly with Qt 6 and KDE Plasma D-Bus APIs, respecting system themes, high-DPI scaling, and Wayland/X11 sessions.

> **Disclaimer:** Lumen is an independent open-source project. It is not affiliated with, sponsored by, or endorsed by Omarchy, Basecamp, or 37signals.

---

## ✨ Features

* 🚀 **Instant Application Launching**: Discovers `.desktop` applications from system, user, Flatpak, and Snap directories with live filesystem watching (`QFileSystemWatcher`).
* 🎯 **Intelligent Fuzzy & Acronym Matching**: Subsequence matching with word-boundary bonuses and acronym recognition (e.g. `ksp` for `KSystemLog`, `ff` for `Firefox`).
* 🌲 **Nested Command Groups & Submenus**: Group commands logically (`Development`, `Docker`, `Git`, `System`) with interactive drill-down (`Tab` / `Right`) or direct unified search.
* ⚡ **KDE System Actions**: Built-in actions for Lock, Logout, Suspend, Restart, Shutdown, and instant access to KDE System Settings panels.
* 🧮 **Instant Calculator**: Safe arithmetic, percentages (`15% of 400`), trigonometry, powers, and roots (`sqrt(144)`) with one-press copy to clipboard.
* 📁 **Common Locations & Recent Files**: Rapid navigation to standard folders (Home, Downloads, Documents, etc.) and recently used documents (`recently-used.xbel`).
* 📋 **Clipboard Search**: Integrates directly with KDE clipboard history without spawning competing daemons.
* 🌐 **Fallback Web Search**: Intelligently falls back to searching your query in your configured default browser.
* 🎨 **Breeze & Adaptive Theme**: Seamlessly adapts to KDE dark and light color schemes with subtle elevation and typography.
* 🤖 **AI-Agent Ready**: Clear JSONC configuration, validated by JSON Schema, with zero opaque runtime state.

---

## ⌨️ Keyboard Navigation

| Key | Action |
|---|---|
| `Meta + Space` (Super+Space) | Toggle Lumen launcher window |
| `Up` / `Down` (or `Ctrl+P` / `Ctrl+N`) | Navigate search results |
| `Enter` | Launch selected item / execute command / copy calculation |
| `Tab` / `Right Arrow` | Open selected category / command group |
| `Backspace` (in sub-level) | Go back to root launcher level |
| `Escape` | Dismiss / close launcher |

---

## 📦 Installation & Setup

### Prerequisites
* **KDE Plasma 6** (or Plasma 5.27+)
* **Python 3.10+** with **PyQt6** (`python3-pyqt6` on Debian/Ubuntu/Kubuntu)
* `git`

### Quick Install
```bash
# Clone the repository
git clone https://github.com/VaibhavPandit-09/lumen.git
cd lumen

# Run directly
python3 -m lumen

# Install to user environment (~/.local/bin and desktop entry)
./install.sh
```

### Global Shortcut Setup (Meta + Space)
In KDE Plasma:
1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts** (or **Shortcuts** → **Add New** → **Command**).
2. Set Command to: `lumen toggle` (or `/home/<user>/.local/bin/lumen toggle`).
3. Set Shortcut to: `Meta + Space`.
4. Click **Apply**.

---

## 🛠️ Configuration & Custom Commands

Lumen stores its configuration in human-readable JSONC (JSON with comments) under `~/.config/lumen/`:
* `~/.config/lumen/config.jsonc` — General preferences (window size, opacity, providers, hidden applications).
* `~/.config/lumen/commands.jsonc` — Custom commands and nested menus.

### Example `commands.jsonc`
```jsonc
{
  "$schema": "https://raw.githubusercontent.com/VaibhavPandit-09/lumen/main/lumen/core/schema.json",
  "commands": [
    {
      "name": "Restart Docker Containers",
      "description": "Restart development containers via docker compose",
      "icon": "docker",
      "category": "Development",
      "command": "docker compose restart",
      "terminal": false
    },
    {
      "name": "Git Prune Local Branches",
      "description": "Delete merged local git branches",
      "icon": "vcs-branch",
      "category": "Development",
      "command": "git branch --merged | grep -v '\\*\\|master\\|main' | xargs -n 1 git branch -d",
      "terminal": true
    },
    {
      "name": "Dev Workspaces",
      "description": "Nested development projects",
      "icon": "folder-development",
      "category": "Workspaces",
      "subcommands": [
        {
          "name": "Open Lumen Project",
          "description": "Open Lumen in code editor",
          "icon": "code-oss",
          "command": "code ~/workspace/gitdev/lumen"
        }
      ]
    }
  ]
}
```

For full configuration options, see the [Configuration Guide](docs/CONFIGURATION.md) and [Agent Guide](docs/AGENT_GUIDE.md).

---

## 🧪 Testing

Lumen comes with an automated unit and integration test suite:

```bash
# Run tests headlessly
make test

# Or using standard unittest
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📖 Documentation

* [Architecture Blueprint](docs/ARCHITECTURE.md)
* [Agent-First Development Guide](docs/AGENT_GUIDE.md)
* [Configuration Specification](docs/CONFIGURATION.md)
* [Installation & Packaging](docs/INSTALLATION.md)

---

## 🤝 Contributing

Contributions are warmly welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on code style, testing, and pull requests.

---

## 📄 License

Lumen is open-source software licensed under the [MIT License](LICENSE).
