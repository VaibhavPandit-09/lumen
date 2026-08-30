#!/usr/bin/env bash
# Lumen Local User Uninstallation Script
set -e

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"

echo "=== Uninstalling Lumen ==="

if [ -f "$BIN_DIR/lumen" ]; then
    rm -f "$BIN_DIR/lumen"
    echo "✓ Removed $BIN_DIR/lumen"
fi

if [ -f "$APP_DIR/lumen.desktop" ]; then
    rm -f "$APP_DIR/lumen.desktop"
    echo "✓ Removed $APP_DIR/lumen.desktop"
fi

echo ""
echo "Note: Configuration files in ~/.config/lumen were preserved."
echo "If you wish to remove them, run: rm -rf ~/.config/lumen"
echo "=== Uninstallation Complete ==="
