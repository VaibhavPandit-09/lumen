# Upgrading, Migration & Lifecycle Guide for Lumen

This document details how Lumen manages application updates, configuration migrations, custom action preservation, and clean uninstallation.

---

## 1. Zero Data Loss Guarantee

When you upgrade Lumen to a new version, your personal data is **strictly preserved**:
* `~/.config/lumen/config.jsonc` (User configuration & preferences)
* `~/.config/lumen/commands.jsonc` (Custom user commands & submenus)
* `~/.config/lumen/actions/` (All user-created action manifests)

The installation scripts and package managers never overwrite user files in `~/.config/lumen`.

---

## 2. Upgrading Lumen

### From Git Source (Recommended User-Local)
```bash
cd ~/workspace/gitdev/lumen  # or your clone directory
git pull origin main
./install.sh
```

During execution, `install.sh` will:
1. Detect your existing Lumen installation and current version.
2. Gracefully stop any running Lumen background daemon to avoid file locks or stale sockets.
3. Update executable wrappers and desktop integration.
4. Retain your existing configuration files and custom action manifests.
5. Verify the updated binary and run post-install diagnostics.

---

## 3. Configuration Migrations & Automatic Backups

Lumen includes an automatic configuration versioning and migration engine (`ConfigMigrator`).

* **Version Tracking**: The `config_version` field in `config.jsonc` tracks the configuration schema format.
* **Automatic Backups**: Before applying any schema migration, Lumen automatically creates a timestamped backup:
  `~/.config/lumen/config.jsonc.backup-YYYYMMDD-HHMMSS`
* **Retention Pruning**: Lumen automatically prunes old backups, keeping only the 5 most recent backups to prevent disk clutter.
* **Safe Fallbacks**: If an older configuration contains custom user keys, they are safely preserved during migration.

---

## 4. Troubleshooting & System Health (`lumen doctor`)

After upgrading, you can run the built-in diagnostic engine to verify your installation:

```bash
# Human-readable diagnostic report
lumen doctor

# JSON format for automated agents and scripts
lumen doctor --json
```

The diagnostic engine validates:
* Python runtime version (>= 3.10)
* PyQt6 bindings availability
* Desktop session type (KDE Plasma Wayland/X11)
* PATH environment configuration
* Executable wrapper integrity
* Desktop entry and icon registration
* Configuration syntax and schema compliance
* Custom action manifest validity
* Single-instance daemon IPC socket status

---

## 5. Rollback & Recovery

If you ever need to roll back to a previous configuration backup:

1. List available backups:
   ```bash
   ls -lt ~/.config/lumen/config.jsonc.backup-*
   ```
2. Restore the desired backup:
   ```bash
   cp ~/.config/lumen/config.jsonc.backup-<TIMESTAMP> ~/.config/lumen/config.jsonc
   ```
3. Reload Lumen:
   ```bash
   lumen actions reload
   ```

---

## 6. Uninstallation & Purge

### Normal Uninstallation (Preserves User Data)
```bash
./uninstall.sh
```
Removes application binaries, desktop entries, icon assets, and stops running daemon processes. **Your configurations and custom actions remain untouched in `~/.config/lumen`.**

### Complete Purge (Removes User Data)
```bash
./uninstall.sh --purge
```
Prompts for explicit confirmation before removing `~/.config/lumen`.
