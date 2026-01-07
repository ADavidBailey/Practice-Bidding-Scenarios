#!/bin/bash

# Setup script for PBS Development VS Code extension
# This creates a symlink in the VS Code extensions directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTENSION_NAME="pbs-dev"
VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"

echo "PBS Development Extension Setup"
echo "================================"

# Check if VS Code extensions directory exists
if [ ! -d "$VSCODE_EXTENSIONS_DIR" ]; then
    echo "Creating VS Code extensions directory..."
    mkdir -p "$VSCODE_EXTENSIONS_DIR"
fi

# Target symlink path
SYMLINK_PATH="$VSCODE_EXTENSIONS_DIR/$EXTENSION_NAME"

# Remove existing symlink or directory if it exists
if [ -L "$SYMLINK_PATH" ]; then
    echo "Removing existing symlink..."
    rm "$SYMLINK_PATH"
elif [ -d "$SYMLINK_PATH" ]; then
    echo "Removing existing directory..."
    rm -rf "$SYMLINK_PATH"
fi

# Create symlink
echo "Creating symlink: $SYMLINK_PATH -> $SCRIPT_DIR"
ln -s "$SCRIPT_DIR" "$SYMLINK_PATH"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Extension installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Run 'npm install' in $SCRIPT_DIR (if not already done)"
    echo "2. Run 'npm run compile' to build the extension"
    echo "3. Reload VS Code (Cmd+Shift+P -> 'Developer: Reload Window')"
    echo ""
    echo "The PBS sidebar should appear in the Activity Bar."
else
    echo ""
    echo "✗ Failed to create symlink"
    exit 1
fi
