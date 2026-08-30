# Universal Software Management in Lumen

Lumen provides a unified software management platform that abstracts diverse Linux package managers behind a single, consistent interface.

---

## 🎯 Supported Package Backends

| Backend | Platform / Distribution | Discovery Command | Elevation |
|---|---|---|---|
| **APT** | Debian, Ubuntu, Kubuntu, KDE neon, Linux Mint | `apt-cache search` / `dpkg-query` | `pkexec apt-get` |
| **Flatpak** | Universal Linux desktop packages | `flatpak search` / `flatpak list` | User / System Flatpak |
| **Snap** | Ubuntu, Debian, Arch Linux, Fedora | `snap find` / `snap list` | `pkexec snap` |
| **Pacman** | Arch Linux, Manjaro, EndeavourOS | `pacman -Ss` / `pacman -Qs` | `pkexec pacman` |

---

## 💡 Natural Command Intents

Lumen understands natural command intents typed directly into the search bar:

### 1. Installing Software
```text
install <package>
add <package>
get <package>
i <package>
```
*Example*: `install htop`, `install code`, `install vlc`.

### 2. Removing Software
```text
uninstall <package>
remove <package>
rm <package>
purge <package>
```
*Destructive Safeguard*: Removing a package triggers an explicit confirmation prompt in the breadcrumb header:
```text
⚠️ Confirm: Uninstall 'htop'? — Press Enter again or click to execute (Esc to cancel)
```

### 3. Updating Software
```text
update <package>
update all
updates
upgrade all
system updates
```
*Update All*: Queries all active backends (e.g. APT, Flatpak, Snap, Pacman) and presents a unified action to check and apply updates.

---

## 🔐 Security & Privilege Escalation

* **No Root Daemon**: Lumen runs entirely as a standard unprivileged user process.
* **No Password Caching**: Lumen never prompts for or stores user passwords.
* **PolicyKit Integration**: All privileged operations use `pkexec` to invoke standard FreeDesktop/KDE authentication dialogs.
* **Input Sanitization**: Package names are strictly validated against `^[a-zA-Z0-9_\-\.\+]+$` before dispatch.

---

## 💻 CLI Commands

```bash
# Search across all available backends
lumen packages search <query>
lumen packages search <query> --json

# Install package
lumen packages install <package> [--backend apt|flatpak|snap|pacman]

# Remove package
lumen packages remove <package> [--purge]

# Check available updates
lumen packages updates
lumen packages updates --json

# Update all software
lumen update
lumen update --json
```
