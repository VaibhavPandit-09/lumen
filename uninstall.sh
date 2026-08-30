#!/usr/bin/env bash
# ==============================================================================
# Lumen — Production User-Local Uninstallation Script
# An agent-friendly command launcher for KDE Plasma
# ==============================================================================
set -e

BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_DIR/applications"
ICON_DIR="$DATA_DIR/icons/hicolor/scalable/apps"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lumen"
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
UID_VAL="$(id -u 2>/dev/null || echo 1000)"

PURGE=false
CHECK_MODE=false
AUTO_YES=false

for arg in "$@"; do
    case "$arg" in
        --purge)
            PURGE=true
            ;;
        --check)
            CHECK_MODE=true
            ;;
        -y|--yes)
            AUTO_YES=true
            ;;
        --help|-h)
            echo "Usage: ./uninstall.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --purge       Remove user configuration and custom actions in ~/.config/lumen"
            echo "  --check       Preview files that would be removed without modifying anything"
            echo "  -y, --yes     Automatic yes to prompts (for scripted/non-interactive uninstall)"
            echo "  --help, -h    Display this help message"
            echo ""
            echo "Normal uninstallation preserves your user configuration and custom actions."
            exit 0
            ;;
        *)
            echo "Unknown option: $arg (run './uninstall.sh --help' for usage)"
            exit 1
            ;;
    esac
done

echo "=== Uninstalling Lumen ==="

if [ "$CHECK_MODE" = true ]; then
    echo "• Uninstallation preview (dry-run):"
    [ -f "$BIN_DIR/lumen" ] && echo "  - Executable: $BIN_DIR/lumen"
    [ -f "$APP_DIR/lumen.desktop" ] && echo "  - Desktop entry: $APP_DIR/lumen.desktop"
    [ -f "$ICON_DIR/lumen.svg" ] && echo "  - SVG icon: $ICON_DIR/lumen.svg"
    echo "  - Runtime sockets in $RUNTIME_DIR/lumen"
    if [ "$PURGE" = true ]; then
        echo "  - [PURGE] Configuration & actions in $CONFIG_DIR"
    else
        echo "  - [PRESERVE] Configuration & actions in $CONFIG_DIR will NOT be deleted"
    fi
    exit 0
fi

# 1. Terminate running daemon
if command -v lumen > /dev/null 2>&1; then
    lumen hide > /dev/null 2>&1 || true
fi
pkill -f "python3.*-m lumen (daemon|show)" 2>/dev/null || true

# 2. Remove application files
if [ -f "$BIN_DIR/lumen" ]; then
    rm -f "$BIN_DIR/lumen"
    echo "✓ Removed executable wrapper: $BIN_DIR/lumen"
fi

if [ -f "$APP_DIR/lumen.desktop" ]; then
    rm -f "$APP_DIR/lumen.desktop"
    echo "✓ Removed desktop entry: $APP_DIR/lumen.desktop"
fi

if [ -f "$ICON_DIR/lumen.svg" ]; then
    rm -f "$ICON_DIR/lumen.svg"
    echo "✓ Removed SVG icon: $ICON_DIR/lumen.svg"
fi

# 3. Clean up runtime socket directories
rm -rf "$RUNTIME_DIR/lumen" 2>/dev/null || true
rm -rf "/tmp/lumen_$UID_VAL" 2>/dev/null || true

# 4. Refresh desktop database
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache "$DATA_DIR/icons/hicolor" 2>/dev/null || true
fi

# 5. Handle user configuration & actions
if [ "$PURGE" = true ]; then
    if [ "$AUTO_YES" = true ]; then
        rm -rf "$CONFIG_DIR"
        echo "✓ Purged configuration directory: $CONFIG_DIR"
    elif [ -t 0 ]; then
        read -p "⚠️  Are you sure you want to permanently delete all configuration and custom actions in $CONFIG_DIR? (y/N): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
            rm -rf "$CONFIG_DIR"
            echo "✓ Purged configuration directory: $CONFIG_DIR"
        else
            echo "ℹ️  Purge cancelled. User configuration preserved in $CONFIG_DIR"
        fi
    else
        # Non-interactive purge without tty
        rm -rf "$CONFIG_DIR"
        echo "✓ Purged configuration directory: $CONFIG_DIR"
    fi
else
    echo ""
    echo "ℹ️  User configuration and custom actions in $CONFIG_DIR were preserved."
    echo "   To completely remove user data, run: ./uninstall.sh --purge"
fi

echo ""
echo "=== Uninstallation Complete ==="
