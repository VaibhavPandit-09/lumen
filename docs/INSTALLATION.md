# Lumen Installation & Setup Guide

This guide explains how to install, configure, verify, update, and uninstall Lumen on **KDE Plasma**.

---

## 📋 System Requirements

* **Desktop**: KDE Plasma 6 (or Plasma 5.27+)
* **Session**: Wayland or X11
* **Runtime**: Python 3.10 or newer with PyQt6
* **Prerequisites** (Debian / Ubuntu / Kubuntu):
  ```bash
  sudo apt install python3 python3-pyqt6
  ```
* **Prerequisites** (Arch Linux):
  ```bash
  sudo pacman -S python python-pyqt6
  ```
* **Prerequisites** (Fedora):
  ```bash
  sudo dnf install python3 python3-pyqt6
  ```

---

## 🚀 End-User Installation (Recommended)

### 1. User-Local Installation
The recommended way to install Lumen is using the non-root user-local installer:

```bash
git clone https://github.com/VaibhavPandit-09/lumen.git
cd lumen

# Optional: Validate system prerequisites without modifying files
./install.sh --check

# Install to ~/.local/bin and ~/.local/share
./install.sh
```

### 2. Verify System Health
Run `lumen doctor` to verify system health and desktop integration:
```bash
lumen doctor
```

---

## 🛠️ Developer Setup

If you are contributing to Lumen or building new providers:

```bash
git clone https://github.com/VaibhavPandit-09/lumen.git
cd lumen

# Run test suite headlessly
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -p "test_*.py" -v

# Run directly from source tree without installation
python3 -m lumen
```

---

## 📦 Package Distribution

### Debian / Ubuntu (`.deb`)
```bash
# Build package
dpkg-buildpackage -us -uc -b

# Install generated package
sudo dpkg -i ../lumen_0.4.0-1_all.deb
```

### Arch Linux (`PKGBUILD`)
```bash
makepkg -si
```

### Pipx Evaluation
While `pipx` (`pipx install .`) is supported for installing the Python CLI entrypoint into an isolated virtual environment, desktop launcher applications require integrating with FreeDesktop `.desktop` files, scalable icons in `/usr/share/icons` or `~/.local/share/icons`, and KDE system settings. The included `./install.sh` script handles these desktop integrations automatically without requiring root permissions.

---

## ⌨️ Configuring the Global Shortcut (Meta + Space)

To bind Lumen to **`Meta + Space`** (Super+Space) in KDE Plasma:

1. Open **System Settings** (`systemsettings`).
2. Navigate to **Keyboard** → **Shortcuts** (or **Shortcuts** → **Command**).
3. Click **Add New** → **Command**.
4. Configure:
   * **Name**: `Lumen Launcher`
   * **Command**: `~/.local/bin/lumen toggle` (or `lumen toggle`)
   * **Shortcut**: `Meta+Space`
5. Click **Apply**.

Now pressing `Meta + Space` will instantly open or toggle Lumen!

---

## 🔄 Running as a Background Daemon (Optional)

Lumen includes a single-instance daemon mode:
```bash
# Start background daemon
lumen daemon &
```

To autostart Lumen when logging into KDE Plasma:
1. Open **System Settings** → **Autostart**.
2. Click **Add...** → **Add Application...** → select **Lumen**.
3. Click **OK**.

---

## 🗑️ Uninstallation

### Normal Uninstallation (Preserves Configuration & Custom Actions)
```bash
./uninstall.sh
```

### Complete Purge (Removes Configuration & Custom Actions)
```bash
./uninstall.sh --purge
```

See [docs/UPGRADING.md](file:///home/vaibhavp/workspace/gitdev/lumen/docs/UPGRADING.md) for full upgrade and migration instructions.
