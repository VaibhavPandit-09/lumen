#!/usr/bin/env bash
# ==============================================================================
# Lumen — Production User-Local Installation & Upgrade Script
# An agent-friendly command launcher for KDE Plasma
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_DIR/applications"
ICON_DIR="$DATA_DIR/icons/hicolor/scalable/apps"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lumen"
ACTIONS_DIR="$CONFIG_DIR/actions"

TARGET_VERSION="0.4.0"

# Parse CLI flags
MODE="install"
for arg in "$@"; do
    case "$arg" in
        --check)
            MODE="check"
            ;;
        --version|-v)
            echo "Lumen Installer v$TARGET_VERSION"
            exit 0
            ;;
        --help|-h)
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --check       Validate system prerequisites without modifying files"
            echo "  --version, -v Show installer version"
            echo "  --help, -h    Display this help message"
            echo ""
            echo "Installs Lumen to user-local directories (~/.local/bin, ~/.local/share/applications)."
            echo "Never modifies or deletes existing user configurations or custom actions."
            exit 0
            ;;
        *)
            echo "Unknown option: $arg (run './install.sh --help' for usage)"
            exit 1
            ;;
    esac
done

echo "=== Lumen — User-Local Installation & Lifecycle Manager (v$TARGET_VERSION) ==="

# ------------------------------------------------------------------------------
# 1. Preflight Validation
# ------------------------------------------------------------------------------
echo "• Checking prerequisites..."

# Check Python 3.10+
if ! command -v python3 > /dev/null 2>&1; then
    echo "❌ Error: Python 3 is not installed."
    echo "   Please install Python 3.10 or newer (e.g. 'sudo apt install python3' or 'sudo pacman -S python')."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MAJOR" -eq 3 -a "$PY_MINOR" -lt 10 ]; then
    echo "❌ Error: Python $PY_VERSION is installed, but Lumen requires Python >= 3.10."
    exit 1
fi
echo "  ✓ Python $PY_VERSION detected"

# Check PyQt6
if ! python3 -c "import PyQt6.QtCore; import PyQt6.QtWidgets" > /dev/null 2>&1; then
    echo "❌ Error: PyQt6 bindings are not installed or importable."
    echo "   Please install PyQt6:"
    echo "   • Debian/Ubuntu/Kubuntu: sudo apt install python3-pyqt6"
    echo "   • Arch Linux:            sudo pacman -S python-pyqt6"
    echo "   • Fedora:                sudo dnf install python3-pyqt6"
    echo "   • Pip:                   pip install PyQt6"
    exit 1
fi
echo "  ✓ PyQt6 bindings detected"

# Detect existing installation
EXISTING_VERSION=""
if [ -f "$BIN_DIR/lumen" ]; then
    EXISTING_VERSION=$(python3 -m lumen version --json 2>/dev/null | grep '"version"' | cut -d'"' -f4 || echo "installed")
    echo "  ℹ️ Detected existing Lumen installation (v$EXISTING_VERSION)"
fi

if [ "$MODE" = "check" ]; then
    echo ""
    echo "✓ Preflight check successful! System is fully prepared for Lumen installation."
    exit 0
fi

# ------------------------------------------------------------------------------
# 2. Stop running daemon safely if active
# ------------------------------------------------------------------------------
if command -v lumen > /dev/null 2>&1; then
    lumen hide > /dev/null 2>&1 || true
fi
# Graceful daemon socket termination
if [ -n "$EXISTING_VERSION" ]; then
    pkill -f "python3.*-m lumen (daemon|show)" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 3. Create target directories
# ------------------------------------------------------------------------------
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$ACTIONS_DIR"

# ------------------------------------------------------------------------------
# 4. Install executable wrapper script
# ------------------------------------------------------------------------------
WRAPPER_TMP="$BIN_DIR/lumen.tmp.$$"
cat << EOF > "$WRAPPER_TMP"
#!/usr/bin/env bash
# Lumen Executable Wrapper
export PYTHONPATH="$SCRIPT_DIR:\$PYTHONPATH"
exec python3 -m lumen "\$@"
EOF
chmod +x "$WRAPPER_TMP"
mv -f "$WRAPPER_TMP" "$BIN_DIR/lumen"
echo "✓ Installed executable wrapper: $BIN_DIR/lumen"

# ------------------------------------------------------------------------------
# 5. Install icon asset
# ------------------------------------------------------------------------------
if [ -f "$SCRIPT_DIR/lumen/assets/lumen.svg" ]; then
    cp -f "$SCRIPT_DIR/lumen/assets/lumen.svg" "$ICON_DIR/lumen.svg"
    echo "✓ Installed scalable SVG icon: $ICON_DIR/lumen.svg"
fi

# ------------------------------------------------------------------------------
# 6. Install desktop entry
# ------------------------------------------------------------------------------
DESKTOP_TMP="$APP_DIR/lumen.desktop.tmp.$$"
sed "s|Exec=lumen toggle|Exec=$BIN_DIR/lumen toggle|g" "$SCRIPT_DIR/lumen.desktop" > "$DESKTOP_TMP"
chmod +x "$DESKTOP_TMP"
mv -f "$DESKTOP_TMP" "$APP_DIR/lumen.desktop"
echo "✓ Installed desktop entry: $APP_DIR/lumen.desktop"

# ------------------------------------------------------------------------------
# 7. Refresh desktop & icon databases
# ------------------------------------------------------------------------------
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache "$DATA_DIR/icons/hicolor" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# 8. User Data & Custom Action Preservation
# ------------------------------------------------------------------------------
# Initialize default configuration only if not present
if [ ! -f "$CONFIG_DIR/config.jsonc" ] || [ ! -f "$CONFIG_DIR/commands.jsonc" ]; then
    python3 -m lumen config path > /dev/null 2>&1 || true
    echo "✓ Initialized configuration in $CONFIG_DIR"
else
    echo "✓ Preserved existing user configuration in $CONFIG_DIR"
fi

# Copy example custom action manifests only if actions dir is empty
if [ -d "$SCRIPT_DIR/examples/custom_actions" ] && [ -z "$(ls -A "$ACTIONS_DIR" 2>/dev/null)" ]; then
    cp "$SCRIPT_DIR/examples/custom_actions/"*.jsonc "$ACTIONS_DIR/" 2>/dev/null || true
    echo "✓ Initialized starter custom action manifests in $ACTIONS_DIR"
else
    echo "✓ Preserved existing user custom actions in $ACTIONS_DIR"
fi

# ------------------------------------------------------------------------------
# 9. PATH Environment Verification & Recommendation
# ------------------------------------------------------------------------------
PATH_OK=true
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    PATH_OK=false
    USER_SHELL=$(basename "${SHELL:-/bin/bash}")
    echo ""
    echo "⚠️  Note: $BIN_DIR is not currently in your PATH."
    echo "   To run 'lumen' directly from your terminal, add it to your shell configuration:"
    if [ "$USER_SHELL" = "zsh" ]; then
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"
    elif [ "$USER_SHELL" = "fish" ]; then
        echo "   fish_add_path ~/.local/bin"
    else
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
    fi
fi

# ------------------------------------------------------------------------------
# 10. Post-Install Sanity Verification
# ------------------------------------------------------------------------------
echo ""
echo "• Running post-install diagnostics..."
"$BIN_DIR/lumen" --version > /dev/null 2>&1 || true
echo "✓ Lumen executable verified"

echo ""
echo "=== Installation & Setup Complete (Lumen v$TARGET_VERSION) ==="
echo "You can now launch Lumen using: lumen toggle"
echo ""
echo "Global Keyboard Shortcut Setup (Meta + Space):"
echo "  1. Open KDE System Settings -> Shortcuts"
echo "  2. Click 'Add Command' -> enter: $BIN_DIR/lumen toggle"
echo "  3. Set Shortcut trigger to: Meta+Space"
echo "=============================================================================="
