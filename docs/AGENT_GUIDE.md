# Agent-First Development & Customization Guide

One of **Lumen's defining characteristics is malleability**.

Lumen is engineered so that **AI coding agents** can easily inspect the system, understand user configurations, and extend the user's desktop launcher through ordinary, readable files.

---

## 🧭 Core Principles for AI Agents

1. **Human-Readable JSONC**: Configuration is stored in `~/.config/lumen/config.jsonc` and `~/.config/lumen/commands.jsonc`. Both support comments (`//` and `/* */`).
2. **Schema-Backed**: All configurations validate against `lumen/core/schema.json`.
3. **No Binary Databases**: Everything is file-based. Adding a command or menu requires no database migrations.
4. **Instant Live Reload**: Changes to `commands.jsonc` or calling `lumen config add-command` reload into the running launcher immediately.

---

## 🗺️ Repository Map

```
lumen/
├── assets/             # Vector icon assets (lumen.svg)
├── core/               # Matching, scanning, configuration, logging, and execution
│   ├── actions/        # Custom action scripting & dispatch engine
│   │   ├── discovery.py  # Action scanner & mtime cache
│   │   ├── dispatcher.py # Canonical ActionDispatcher routing all item execution
│   │   ├── executor.py   # Safe execution & timeout manager
│   │   ├── manifest.py   # ActionDefinition & manifest loader
│   │   └── validator.py  # Contract validation & diagnostics
│   ├── packages/       # Universal software management subsystem
│   │   ├── apt.py        # APT & Dpkg backend
│   │   ├── base.py       # BasePackageBackend & PackageInfo models
│   │   ├── flatpak.py    # Flatpak backend
│   │   ├── intent.py     # Natural command intent parser
│   │   ├── manager.py    # Multi-backend aggregator & concurrency lock
│   │   ├── pacman.py     # Pacman & ALPM backend
│   │   └── snap.py       # Snap backend
│   ├── app_scanner.py  # XDG .desktop parsing, caching, and watching
│   ├── calculator.py   # AST-based safe math & percentage evaluation
│   ├── config.py       # JSONC config parser, schema validation, and migrations
│   ├── doctor.py       # Health diagnostics & system inspection engine
│   ├── fuzzy.py        # Multi-tier fuzzy & acronym search engine
│   ├── logging.py      # Privacy-preserving diagnostic logging
│   ├── models.py       # SearchResult, CommandItem, ItemCategory models
│   ├── runner.py       # Detached process, clipboard, and terminal runner
│   ├── schema.json     # Formal configuration schema
│   └── units.py        # Physical, time, and data unit conversion engine
├── providers/          # Modular search providers
│   ├── actions.py      # Custom action search provider
│   ├── applications.py # Desktop application provider
│   ├── base.py         # BaseProvider with safe_search error boundary
│   ├── calculator.py   # Math calculation provider
│   ├── clipboard.py    # Clipboard integration provider
│   ├── commands.py     # Custom user/agent commands & submenus
│   ├── conversions.py  # Physical & data unit conversions
│   ├── currency.py     # Cached currency conversions
│   ├── krunner.py      # Optional KDE Plasma KRunner D-Bus adapter
│   ├── locations.py    # Standard folders provider
│   ├── packages.py     # Software search & natural intent provider
│   ├── recent_files.py # FreeDesktop recent documents (.xbel)
│   ├── system_actions.py # KDE session & settings actions
│   └── web_search.py   # Fallback browser search provider
├── service/            # Lifecycle & IPC daemon
│   ├── daemon.py       # Single-instance Unix socket server
│   └── shortcuts.py    # Global shortcut helpers (Alt+Space)
├── ui/                 # PyQt6 command palette interface
│   ├── animations.py   # Subtle 120ms window transitions
│   ├── launcher_window.py # Main floating overlay window
│   ├── result_list.py  # High-performance custom item delegate (NoFocus)
│   ├── search_bar.py   # Keyboard-first search input widget
│   ├── theme.py        # Breeze theme & color scheme engine
│   └── tray.py         # Optional KDE Plasma system tray companion
└── tests/              # 112+ unit & headless integration tests
```

---

## 🛠️ AI Agent Guide: Adding a Custom Action

To add a new command workflow without touching Lumen source code:

1. Create a `.jsonc` file in `~/.config/lumen/actions/<id>.jsonc` (e.g. `restart_service.jsonc`):
```jsonc
{
  "id": "restart-service",
  "name": "Restart Dev Service",
  "description": "Restarts the backend API service",
  "category": "Development",
  "icon": "system-reboot",
  "keywords": ["service", "api", "restart"],
  "exec": ["systemctl", "--user", "restart", "my-api.service"],
  "confirm": false,
  "timeout_seconds": 10
}
```
2. Validate using the CLI:
```bash
lumen actions validate --json
```
3. Test running the action:
```bash
lumen actions run restart-service
```
4. Reload the running launcher daemon:
```bash
lumen actions reload
```

See [docs/EXTENSION_API.md](file:///home/vaibhavp/workspace/gitdev/lumen/docs/EXTENSION_API.md) for full manifest specification.

---

## 📂 Configuration Paths

---

## 🛠️ Common Agent Tasks & Recipes

### 1. "Add a command to restart my Docker development environment"

Add the following object to the `commands` list in `~/.config/lumen/commands.jsonc`:

```jsonc
{
  "name": "Restart Docker Services",
  "description": "Restart local docker compose containers",
  "icon": "docker",
  "category": "Development",
  "command": "docker compose restart",
  "terminal": false
}
```

Or execute via CLI:
```bash
python3 -m lumen config add-command \
  --name "Restart Docker Services" \
  --cmd "docker compose restart" \
  --desc "Restart local docker compose containers" \
  --category "Development"
```

---

### 2. "Add a command to open my project in VS Code"

```jsonc
{
  "name": "Open Project in VS Code",
  "description": "Open workspace in Visual Studio Code",
  "icon": "code-oss",
  "category": "Workspaces",
  "command": "code ~/workspace/gitdev/myproject",
  "keywords": ["project", "code", "editor", "workspace"]
}
```

---

### 3. "Create a Development submenu"

To create a nested submenu, define a command item containing `subcommands`:

```jsonc
{
  "name": "Development Tools",
  "description": "Quick actions for local development",
  "icon": "applications-development",
  "category": "Development",
  "subcommands": [
    {
      "name": "Start Dev Server",
      "description": "Run development server on port 3000",
      "icon": "utilities-terminal",
      "command": "npm run dev",
      "terminal": true,
      "cwd": "~/workspace/myproject"
    },
    {
      "name": "Run Test Suite",
      "description": "Execute automated unit tests",
      "icon": "system-run",
      "command": "make test",
      "terminal": true
    },
    {
      "name": "Show Docker Logs",
      "description": "Follow docker container output",
      "icon": "utilities-terminal",
      "command": "docker compose logs -f",
      "terminal": true
    }
  ]
}
```

---

### 4. "Add a command that connects to my development server over SSH"

```jsonc
{
  "name": "SSH Dev Server",
  "description": "Connect to staging/dev server via SSH",
  "icon": "network-server",
  "category": "SSH",
  "command": "ssh dev@staging.example.internal",
  "terminal": true,
  "keywords": ["ssh", "server", "remote", "staging"]
}
```

---

### 5. "Add a command that shows my Git status & prunes branches"

```jsonc
{
  "name": "Git Prune Branches",
  "description": "Fetch and prune merged local Git branches",
  "icon": "vcs-branch",
  "category": "Git",
  "command": "git fetch -p && git branch --merged | grep -v '\\*\\|master\\|main' | xargs -n 1 git branch -d",
  "terminal": true
}
```

---

### 6. "Hide an application from the launcher"

To hide a `.desktop` application (e.g. `im-config.desktop` or `info.desktop`), add its `.desktop` filename or title to `hidden_applications` in `~/.config/lumen/config.jsonc`:

```jsonc
{
  "hidden_applications": [
    "im-config.desktop",
    "info.desktop",
    "Secret Application"
  ]
}
```

---

### 7. "Change my launcher shortcut"

Update the `shortcut` property in `~/.config/lumen/config.jsonc`:

```jsonc
{
  "shortcut": "Alt+Space"
}
```

---

## 🔒 Security Guidelines for Agents

* **No Remote Scripts**: Never configure Lumen commands to download and immediately execute unverified remote shell scripts (`curl ... | sh`).
* **No Hardcoded Secrets**: Never store API tokens, passwords, or private keys inside `commands.jsonc`. Use environment variables or local keyrings.
* **Detached Execution**: Lumen runs non-terminal commands with `start_new_session=True`. Ensure commands meant to run interactively have `"terminal": true`.
