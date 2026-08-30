#!/usr/bin/env bash
# Lumen Local User Uninstallation Script
set -e

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp}"
UID_VAL="$(id -u 2>/dev/null || echo 1000)"

echo "=== Uninstalling Lumen ==="

# 1. Stop running daemon instance if active
if command -v lumen > /dev/null 2>&1; then
    lumen hide > /dev/null 2>&1 || true
fi
pkill -f "python3 -m lumen" 2>/dev/null || true

# 2. Remove executable and integration files
if [ -f "$BIN_DIR/lumen" ]; then
    rm -f "$BIN_DIR/lumen"
    echo "✓ Removed $BIN_DIR/lumen"
fi

if [ -f "$APP_DIR/lumen.desktop" ]; then
    rm -f "$APP_DIR/lumen.desktop"
    echo "✓ Removed $APP_DIR/lumen.desktop"
fi

if [ -f "$ICON_DIR/lumen.svg" ]; then
    rm -f "$ICON_DIR/lumen.svg"
    echo "✓ Removed $ICON_DIR/lumen.svg"
fi

# 3. Clean up runtime socket directories
rm -rf "$RUNTIME_DIR/lumen" 2>/dev/null || true
rm -rf "/tmp/lumen_$UID_VAL" 2>/dev/null || true

# 4. Refresh desktop database
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo ""
echo "Note: User configuration and custom actions in ~/.config/lumen were preserved."
echo "If you wish to remove them as well, run: rm -rf ~/.config/lumen"
echo "=== Uninstallation Complete ==="
