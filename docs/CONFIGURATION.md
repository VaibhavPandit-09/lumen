# Lumen Configuration Guide

Lumen uses **JSONC** (JSON with Comments) for all configuration settings and custom command definitions.

---

## 📁 File Structure

Configurations are located in:
```
~/.config/lumen/
├── config.jsonc      # General launcher settings
└── commands.jsonc    # Custom commands and nested menus
```

---

## ⚙️ Main Configuration (`config.jsonc`)

| Option | Type | Default | Description |
|---|---|---|---|
| `config_version` | `integer` | `1` | Configuration schema version (used by migration engine) |
| `shortcut` | `string` | `"Meta+Space"` | Global keyboard shortcut trigger |
| `theme` | `string` | `"auto"` | Theme: `"auto"` (follows KDE Breeze), `"dark"`, or `"light"` |
| `window_width` | `integer` | `680` | Launcher window width in pixels (400 - 1400) |
| `max_results` | `integer` | `9` | Maximum visible search items (3 - 25) |
| `opacity` | `number` | `0.98` | Window background opacity (0.5 to 1.0) |
| `show_badges` | `boolean` | `true` | Display category pill badges (`[App]`, `[Cmd]`, `[Action]`, `[Calc]`, `[Unit]`) |
| `enable_animations` | `boolean` | `true` | Enable subtle window entry/dismissal transitions |
| `animation_duration_ms` | `integer` | `120` | Transition duration in milliseconds (0 - 500) |
| `actions_dir` | `string` | `"~/.config/lumen/actions"` | Directory storing custom action manifests |
| `enable_tray` | `boolean` | `false` | Enable optional KDE system tray companion |
| `providers` | `object` | `{...}` | Toggle individual search providers on or off |
| `hidden_applications` | `array` | `[]` | List of `.desktop` IDs or names to suppress |
| `web_search_engine` | `string` | `"https://duckduckgo.com/?q=%s"` | Fallback web search template URL |
| `calculator_auto_evaluate` | `boolean` | `true` | Evaluate math expressions in search bar |

### Providers Object
```jsonc
"providers": {
  "applications": true,
  "commands": true,
  "actions": true,
  "system_actions": true,
  "locations": true,
  "calculator": true,
  "conversions": true,
  "currency": true,
  "recent_files": true,
  "clipboard": true,
  "web_search": true,
  "krunner": true
}
```

---

## 💻 Commands Configuration (`commands.jsonc`)

Each item in the `commands` array can have the following properties:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Display title in search results |
| `description` | `string` | No | Subtitle / secondary explanation |
| `command` | `string` | No* | Shell command to execute (*required unless `subcommands` is present) |
| `icon` | `string` | No | FreeDesktop icon name (e.g. `docker`, `utilities-terminal`) or image path |
| `category` | `string` | No | Category name for grouping |
| `terminal` | `boolean` | No | `true` to execute inside a terminal window |
| `cwd` | `string` | No | Working directory for the command |
| `env` | `object` | No | Custom environment variables dictionary |
| `keywords` | `array` | No | Extra keywords for fuzzy matching |
| `subcommands` | `array` | No | Nested child command items |
