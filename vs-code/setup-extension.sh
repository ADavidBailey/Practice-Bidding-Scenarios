#!/bin/bash
# Setup script for Practice Bidding Scenarios VS Code extension
# Creates a symlink for local development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTENSION_NAME="practice-bidding-scenarios"
VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"

echo "Setting up PBS VS Code extension for local development..."

# Check if VS Code extensions directory exists
if [ ! -d "$VSCODE_EXTENSIONS_DIR" ]; then
    echo "Creating VS Code extensions directory..."
    mkdir -p "$VSCODE_EXTENSIONS_DIR"
fi

# Check if symlink or directory already exists
LINK_PATH="$VSCODE_EXTENSIONS_DIR/$EXTENSION_NAME"
if [ -L "$LINK_PATH" ]; then
    echo "Removing existing symlink..."
    rm "$LINK_PATH"
elif [ -d "$LINK_PATH" ]; then
    echo "Warning: A directory already exists at $LINK_PATH"
    echo "Please remove it manually and run this script again."
    exit 1
fi

# Create symlink
echo "Creating symlink..."
ln -sf "$SCRIPT_DIR" "$LINK_PATH"

echo ""
echo "Success! Extension symlinked to: $LINK_PATH"
echo ""
echo "Next steps:"
echo "  1. cd to the vs-code directory: cd \"$SCRIPT_DIR\""
echo "  2. Install dependencies: npm install"
echo "  3. Compile the extension: npm run compile"
echo "  4. Restart VS Code to load the extension"
echo ""
echo "For development:"
echo "  - Run 'npm run watch' to auto-compile on changes"
echo "  - After code changes, reload VS Code window (Cmd+Shift+P > 'Developer: Reload Window')"
