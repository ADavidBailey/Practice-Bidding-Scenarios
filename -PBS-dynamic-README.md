# PBS Dynamic Layout System

**Version:** 2.0
**File:** `-PBS-dynamic.txt`

## Overview

The PBS Dynamic Layout System is a BBOalert plugin that dynamically generates Practice Bidding Scenarios buttons at runtime. Instead of using a static, pre-built button list, it fetches the layout configuration and PBS metadata from GitHub each time the plugin loads.

## Features

- **Dynamic Button Generation**: Buttons are created at runtime based on layout configuration files
- **Live Metadata Loading**: Button text and styling are fetched from individual PBS files
- **Missing File Detection**: Buttons for missing PBS files are displayed with red text
- **Test Mode**: Optional diagnostic features for development
- **Instant Config Reload**: Changing settings immediately rebuilds the button list
- **Expand/Collapse**: Section headers collapse/expand their contents; master header toggles all

## Configuration

Access plugin settings via BBOalert's config menu (select "PBS Dynamic Layout"):

| Setting | Description |
|---------|-------------|
| **Enable_Test_Mode** | Shows diagnostic sections and pbs-test folder buttons |
| **Use_Beta_Layout** | Switches from release layout to beta layout file |

Settings take effect immediately - no page refresh required.

## File Structure

```
Practice-Bidding-Scenarios/
├── btn/
│   ├── -button-layout-release.txt   # Production layout
│   └── -button-layout-beta.txt      # Beta/testing layout
├── pbs-beta/                         # Release-ready .pbs files
│   ├── Stayman.pbs
│   ├── Minor_Suit_Opener.pbs
│   └── ...
├── pbs-test/                         # Development .pbs files
│   └── ...
└── -PBS-dynamic.txt                  # This plugin
```

## Layout File Format

Layout files define the button structure using a simple text format:

```
# Comment line

[Major] Title                           # Yellow header (LemonChiffon)
[Major] Title|URL                       # Yellow header with link

[Section] Title                         # Blue collapsible header (lightblue)

[Action] Text|%scriptName%|width        # Green action button (lightgreen)

filename1,            filename2         # Two buttons at 50% each
filename:blue                           # Button with blue text
filename:blue:38%                       # Button with blue text, 38% width
---                                     # Separator/placeholder

(btn1:blue, btn2:blue, btn3:blue)       # Grouped buttons share 50% width
filename1, (btn2:blue, btn3:blue)       # 50% + grouped 50%
```

### Layout Elements

| Element | Format | Description |
|---------|--------|-------------|
| Major Header | `[Major] Title` | Yellow (LemonChiffon) full-width header. First one is master expand/collapse. |
| Section Header | `[Section] Title` | Blue (lightblue) collapsible section header |
| Action Button | `[Action] Text\|script\|width` | Green (lightgreen) button that runs a script |
| Button Row | `name1, name2` | Row of scenario buttons (default 50% each) |
| Separator | `---` | Placeholder/divider button |
| Grouped | `(a, b, c)` | Multiple buttons sharing one 50% slot |

### Button Modifiers

- `:blue` - Sets text color to blue
- `:38%` - Sets explicit width percentage
- Combine: `filename:blue:12%`

## PBS File Format

Each `.pbs` file in `pbs-beta/` or `pbs-test/` contains:

```
Script,AliasName
setDealerCode(`
... dealer code here ...
`, "N", true);
Script

Button,Button Text,chat message%AliasName%,backgroundColor=white width=50%
```

The dynamic system extracts:
- **Button text** from the `Button,` line
- **Styling** from after the `%alias%` pattern

## Test Mode Features

When **Enable_Test_Mode** is checked:

### 1. TEST: pbs-test/ Section
Shows buttons for all `.pbs` files in the `pbs-test/` folder. These are scenarios under active development.

### 2. MISSING PBS FILES Section
Lists buttons referenced in the layout file that don't have corresponding `.pbs` files in `pbs-beta/`. Displayed with:
- Light salmon (lightsalmon) header
- Red text on missing buttons

### 3. ORPHAN SCENARIOS Section
Lists `.pbs` files in `pbs-beta/` that aren't referenced by any button in the layout. Displayed with:
- Plum colored header
- Purple text on orphan buttons
- Buttons are still clickable to test the scenarios

## How It Works

### Initialization Flow

1. Load saved config from localStorage
2. Fetch layout file (release or beta based on setting)
3. Parse layout and create buttons synchronously (preserves order)
4. Fetch PBS metadata asynchronously (updates button text/style)
5. If test mode: insert test buttons and diagnostic sections
6. Set up expand/collapse handlers
7. Collapse all sections initially

### Config Change Detection

The plugin uses an `onAnyMutation` handler to detect when config changes:

1. Compares current localStorage config to last known state
2. If changed, clears all dynamic buttons
3. Re-fetches layout file
4. Rebuilds all buttons with new settings

## GitHub URLs

| Resource | URL Pattern |
|----------|-------------|
| Layout (release) | `raw.githubusercontent.com/.../btn/-button-layout-release.txt` |
| Layout (beta) | `raw.githubusercontent.com/.../btn/-button-layout-beta.txt` |
| PBS files | `raw.githubusercontent.com/.../pbs-beta/{name}.pbs` |
| Test files | `raw.githubusercontent.com/.../pbs-test/{name}.pbs` |
| Directory listing | `api.github.com/repos/.../contents/pbs-beta` |

## Expand/Collapse Behavior

- **Yellow header** (first `[Major]`): Master toggle - expands/collapses ALL scenario buttons
- **Blue headers** (`[Section]`): Toggle buttons within that section only
- **Initial state**: All sections start collapsed

## Troubleshooting

### Buttons not appearing
- Check browser console for "PBS Dynamic" log messages
- Verify GitHub raw URLs are accessible
- Check for JavaScript errors

### Missing file shown in red
- The layout references a file that doesn't exist in `pbs-beta/`
- Either add the missing `.pbs` file or remove the button from the layout

### Config changes not taking effect
- Ensure you click OK in the config dialog (not just close it)
- Check console for "Config changed, triggering rebuild" message

### Buttons in wrong order
- Buttons are created synchronously to preserve layout order
- Metadata (text/style) loads asynchronously and updates in place

## Version History

- **v2.0**: Added immediate rebuild on config change
- **v1.9**: Added missing/orphan diagnostics, beta layout toggle
- **v1.8**: Added expand/collapse, start collapsed
- **v1.7**: Reordered test buttons after action buttons
- **v1.0**: Initial dynamic layout system
