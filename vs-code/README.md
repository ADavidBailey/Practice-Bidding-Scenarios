# Practice Bidding Scenarios VS Code Extension

A VS Code extension for managing Practice Bidding Scenarios (PBS) files for bridge bidding practice.

## Features

### Button Panel Sidebar

The extension adds a sidebar view called "PBS Button Panel" that displays all the button definitions from your PBS files, organized by sections as defined in your `-PBS.txt` configuration file.

- **Sections**: Collapsible sections matching the original panel organization (Minor Suit Sequences, Major Suit Sequences, etc.)
- **Buttons**: Each button shows the scenario label with a tooltip showing the full description
- **Quick Navigation**: Click any button to open its PBS file at the button definition

### File Watching

The extension automatically refreshes when you:
- Modify a PBS file
- Add or remove PBS files
- Update the `-PBS.txt` configuration

## Usage

1. Open the Practice-Bidding-Scenarios workspace in VS Code
2. Click the PBS icon in the Activity Bar (left sidebar)
3. Expand sections to see available bidding scenarios
4. Click a button to open its PBS file

## Commands

- **PBS: Refresh Button Panel** - Manually refresh the button panel

## Development

### Prerequisites

- Node.js 18+
- VS Code 1.85+

### Building

```bash
cd vs-code
npm install
npm run compile
```

### Running in Development

1. Open the `vs-code` folder in VS Code
2. Press F5 to start debugging
3. A new VS Code window will open with the extension loaded

### Local Installation (Symlink)

For ongoing development without F5 debugging, you can symlink the extension to your VS Code extensions folder. This lets you use the extension in your normal VS Code while making changes:

```bash
cd vs-code
./setup-extension.sh
```

This creates a symlink at `~/.vscode/extensions/practice-bidding-scenarios` pointing to your development folder.

After making code changes:
1. Run `npm run compile` (or use `npm run watch` for auto-compile)
2. Reload VS Code window (Cmd+Shift+P > "Developer: Reload Window")

**Note**: The symlink is user-specific and should not be committed to git. Each developer needs to run the setup script once on their machine.

### Packaging

```bash
npm install -g @vscode/vsce
vsce package
```

This creates a `.vsix` file you can install in VS Code.

## File Structure

```
vs-code/
├── src/
│   ├── extension.ts        # Extension entry point
│   ├── buttonPanelProvider.ts  # TreeView provider for sidebar
│   └── pbsParser.ts        # PBS file parser
├── resources/
│   └── pbs-icon.svg        # Sidebar icon
├── package.json            # Extension manifest
└── tsconfig.json           # TypeScript configuration
```

## PBS File Format

The extension parses PBS files looking for `Button` definitions at the end of each file:

```
Button,<label>,\n\
<description line 1>\n\
<description line 2>\n\
%ScriptId%,backgroundColor=lightpink width=100%
```

### Button Properties

- **label**: The display name for the button
- **description**: Multi-line description (using `\n\` for line breaks)
- **scriptId**: Identifier wrapped in `%` (e.g., `%Notrump%`)
- **backgroundColor**: Optional color (lightpink, lightgreen, lightblue, LemonChiffon)
- **width**: Optional width (e.g., `100%`, `38%`)
