# Lumen Extension & Custom Action API

Lumen provides a declarative and modular platform for extending desktop command capabilities without modifying core source code.

Extensions can be created via:
1. **Custom Action Manifests (`~/.config/lumen/actions/*.jsonc`)**: Declarative commands, scripts, and workflows.
2. **Provider Classes (`lumen/providers/`)**: Python plugins implementing the `BaseProvider` interface.

---

## 1. Custom Action Manifest Specification

Place action files in `~/.config/lumen/actions/<action-id>.jsonc`.

### Schema

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "id": "my-action-id",              // Required: alphanumeric, dashes, underscores
  "name": "My Custom Action",        // Required: user-visible display name
  "description": "Short summary",    // Optional: subtitle in launcher
  "category": "Development",         // Optional: default "Actions"
  "icon": "utilities-terminal",      // Optional: Freedesktop icon name
  "keywords": ["tag1", "tag2"],      // Optional: extra search keywords
  "exec": ["command", "arg1"],       // Required: argv list or command string
  "cwd": "~/projects",               // Optional: working directory
  "env": { "FOO": "BAR" },           // Optional: custom environment variables
  "terminal": false,                 // Optional: run inside terminal emulator
  "confirm": false,                  // Optional: require confirmation before run
  "confirm_message": "Are you sure?",// Optional: prompt shown during confirmation
  "timeout_seconds": 15,             // Optional: execution timeout (1-300s)
  "args": [                          // Optional: structured arguments
    {
      "name": "target",
      "description": "Target environment",
      "required": false,
      "default": "staging",
      "choices": ["staging", "production"]
    }
  ]
}
```

---

## 2. Security & Execution Model

* **No Shell String Injection**: Commands are executed directly via `subprocess.run(..., shell=False)`.
* **Argument Substitution**: Placeholders such as `${target}` or `$target` are substituted safely without invoking an intermediate shell.
* **Process Lifecycles & Timeouts**: If a custom script hangs, `timeout_seconds` terminates the child process and logs a clean diagnostic error.
* **Confirmation Guard**: For destructive commands (e.g. deleting files, docker prune, restarting servers), setting `"confirm": true` displays an interactive confirmation step in Lumen before executing.

---

## 3. CLI Inspection & Validation

Developers and AI coding agents can inspect and validate action manifests without launching the GUI:

```bash
# List all discovered actions
lumen actions list

# Output as JSON for agent automation
lumen actions list --json

# Validate all action manifests on disk
lumen actions validate --json

# Inspect a specific action
lumen actions info git-status --json

# Run an action directly
lumen actions run git-status

# Notify running daemon to reload actions
lumen actions reload
```

---

## 4. Authoring Python Providers

To add a provider inside the codebase or plugin layer:

```python
from typing import List
from lumen.core.models import ItemCategory, SearchResult
from lumen.core.runner import open_path_or_url
from lumen.providers.base import BaseProvider

class MyCustomProvider(BaseProvider):
    def __init__(self, enabled: bool = True):
        super().__init__("my_provider", enabled=enabled)

    def search(self, query: str) -> List[SearchResult]:
        if not self.enabled or not query:
            return []

        # Return SearchResult items
        return [
            SearchResult(
                id="my_item_1",
                title=f"Custom Result for '{query}'",
                subtitle="Press Enter to trigger action",
                category=ItemCategory.CUSTOM_ACTION.value,
                icon_name="system-run",
                score=90.0,
                action=lambda: open_path_or_url("https://example.com"),
                badge="Custom",
                origin_provider=self.name,
            )
        ]
```
