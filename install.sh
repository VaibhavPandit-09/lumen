#!/usr/bin/env bash
# Lumen Local User Installation Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
CONFIG_DIR="$HOME/.config/lumen"

echo "=== Installing Lumen — an agent-friendly command launcher for KDE Plasma ==="

# 1. Create target directories
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$CONFIG_DIR"

# 2. Create launcher wrapper script in ~/.local/bin/lumen
cat << EOF > "$BIN_DIR/lumen"
#!/usr/bin/env bash
export PYTHONPATH="$SCRIPT_DIR:\$PYTHONPATH"
exec python3 -m lumen "\$@"
EOF
chmod +x "$BIN_DIR/lumen"
echo "✓ Installed executable wrapper to $BIN_DIR/lumen"

# 3. Install .desktop file
sed "s|Exec=lumen toggle|Exec=$BIN_DIR/lumen toggle|g" "$SCRIPT_DIR/lumen.desktop" > "$APP_DIR/lumen.desktop"
chmod +x "$APP_DIR/lumen.desktop"
echo "✓ Installed desktop entry to $APP_DIR/lumen.desktop"

# 4. Generate default config if not present
if [ ! -f "$CONFIG_DIR/config.jsonc" ] || [ ! -f "$CONFIG_DIR/commands.jsonc" ]; then
    python3 -m lumen config path > /dev/null 2>&1 || true
    echo "✓ Initialized configuration files in $CONFIG_DIR"
fi

echo ""
echo "=== Installation Complete! ==="
echo "You can now run 'lumen' or 'lumen toggle'."
echo "To set up the global shortcut (Meta + Space):"
echo "  1. Open KDE System Settings -> Shortcuts"
echo "  2. Add Command: $BIN_DIR/lumen toggle"
echo "  3. Shortcut: Meta+Space"
echo "=============================="
