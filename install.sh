#!/usr/bin/env bash
# Lumen Local User Installation Script (Idempotent, Safe)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
CONFIG_DIR="$HOME/.config/lumen"

echo "=== Installing Lumen — an agent-friendly command launcher for KDE Plasma ==="

# 1. Create target directories
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$ICON_DIR"
mkdir -p "$CONFIG_DIR"

# 2. Install executable wrapper script in ~/.local/bin/lumen
cat << EOF > "$BIN_DIR/lumen"
#!/usr/bin/env bash
export PYTHONPATH="$SCRIPT_DIR:\$PYTHONPATH"
exec python3 -m lumen "\$@"
EOF
chmod +x "$BIN_DIR/lumen"
echo "✓ Installed executable wrapper to $BIN_DIR/lumen"

# 3. Install icon asset
if [ -f "$SCRIPT_DIR/lumen/assets/lumen.svg" ]; then
    cp "$SCRIPT_DIR/lumen/assets/lumen.svg" "$ICON_DIR/lumen.svg"
    echo "✓ Installed SVG icon to $ICON_DIR/lumen.svg"
fi

# 4. Install .desktop file
sed "s|Exec=lumen toggle|Exec=$BIN_DIR/lumen toggle|g" "$SCRIPT_DIR/lumen.desktop" > "$APP_DIR/lumen.desktop"
chmod +x "$APP_DIR/lumen.desktop"
echo "✓ Installed desktop entry to $APP_DIR/lumen.desktop"

# 5. Update local desktop and icon databases if tools are present
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# 6. Initialize default config if not present
if [ ! -f "$CONFIG_DIR/config.jsonc" ] || [ ! -f "$CONFIG_DIR/commands.jsonc" ]; then
    python3 -m lumen config path > /dev/null 2>&1 || true
    echo "✓ Initialized configuration files in $CONFIG_DIR"
fi

# 7. Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "⚠️  Note: $BIN_DIR is not in your current PATH."
    echo "   Add the following line to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "=== Installation Complete! ==="
echo "You can now run 'lumen' or 'lumen toggle'."
echo "To set up the global shortcut (Meta + Space):"
echo "  1. Open KDE System Settings -> Shortcuts"
echo "  2. Add Command: $BIN_DIR/lumen toggle"
echo "  3. Shortcut: Meta+Space"
echo "=============================="
