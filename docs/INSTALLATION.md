# Lumen Installation & Setup Guide

This guide explains how to install, configure, run, and uninstall Lumen on **KDE Plasma**.

---

## 📋 System Requirements

* **Desktop**: KDE Plasma 6 (or Plasma 5.27+)
* **Session**: Wayland or X11
* **Runtime**: Python 3.10 or newer with PyQt6
* **Packages** (Ubuntu / Kubuntu / Debian):
  ```bash
  sudo apt install python3 python3-pyqt6
  ```

---

## 🚀 Quick Installation

### Method 1: Local User Install (Recommended)

Run the included install script:
```bash
git clone https://github.com/VaibhavPandit-09/lumen.git
cd lumen
./install.sh
```

This will:
1. Link or install the `lumen` executable to `~/.local/bin/lumen`.
2. Install the desktop entry to `~/.local/share/applications/lumen.desktop`.
3. Create default configuration files in `~/.config/lumen/`.

Make sure `~/.local/bin` is in your `$PATH`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## ⌨️ Configuring the Global Shortcut (Meta + Space)

To bind Lumen to **`Meta + Space`** (Super+Space) in KDE Plasma:

1. Open **System Settings** (`systemsettings`).
2. Navigate to **Keyboard** → **Shortcuts** (or **Shortcuts** → **Command**).
3. Click **Add New** → **Command**.
4. Configure:
   * **Name**: `Lumen Launcher`
   * **Command**: `lumen toggle`
   * **Shortcut**: `Meta+Space`
5. Click **Apply**.

Now pressing `Meta + Space` will instantly open or toggle Lumen!

---

## 🔄 Running as a Background Daemon (Optional)

Lumen includes a built-in single-instance daemon mode:
```bash
# Start background daemon
lumen daemon &
```

To autostart Lumen when logging into KDE:
1. Open **System Settings** → **Autostart**.
2. Click **Add...** → **Add Application...** → select **Lumen**.
3. Click **OK**.

---

## 🗑️ Uninstallation

To remove Lumen from your system:

```bash
cd lumen
./uninstall.sh
```

Or manually remove:
```bash
rm -f ~/.local/bin/lumen
rm -f ~/.local/share/applications/lumen.desktop
# Optional: remove configuration and commands
# rm -rf ~/.config/lumen
```
