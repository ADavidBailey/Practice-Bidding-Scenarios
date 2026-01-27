# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Practice Bidding Scenarios (PBS) is a bridge bidding training platform that integrates with Bridge Base Online (BBO). Users define bidding scenarios in PBS format, generate practice hands with constraints using dealer language, and practice bidding with robots or partners. The system transforms scenario definitions through a multi-stage pipeline into bidding sheets and BBO-compatible formats.

## Common Commands

### Development Environment Setup

Required environment variables (add to `~/.zshrc`):
```bash
export WINDOWS_HOST="your-windows-ip"
export WINDOWS_USER="your-windows-username"
export PBS_UNC_PREFIX="\\Mac\Home"  # For Parallels; adjust for your VM
export PBS_BCSCRIPT_PATH="~/Documents/BCScript/2024-11-13"
export PBS_DEALER_PLATFORM="mac"  # or "windows"
```

After setting, run: `source ~/.zshrc`

### VS Code Extension Development

```bash
cd vs-code
npm install
npm run compile      # TypeScript → JavaScript
npm run watch        # Continuous compilation
npm run lint         # ESLint validation
```

### Pipeline Operations

Run from `build-scripts-mac/`:

```bash
# Run all operations on a single scenario
python3 pbs-pipeline-mac.py Smolen "*"

# Run operations from 'bba' to end for all scenarios starting with '1N'
python3 pbs-pipeline-mac.py "1N*" "bba+"

# Run specific operation on a scenario
python3 pbs-pipeline-mac.py "Weak_2_Bids" "pbn"
```

Pipeline operations in order:
1. `dlr` - Extract dealer code from PBS file
2. `pbn` - Generate hands using dealer
3. `rotate` - Create 4-player rotations (PBN and LIN formats)
4. `bba` - Analyze bidding with Bridge Base Archive
5. `filter` - Filter by auction patterns
6. `filterStats` - Generate statistics
7. `biddingSheet` - Generate PDF bidding sheets

### Testing

```bash
# Run basic dealer tests
python3 py/test_dealer.py

# Verify hand consistency
python3 py/VerifyDealerConsistency.py

# Compare PBN files
python3 build-scripts-mac/pbn-diff.py file1.pbn file2.pbn
```

## Architecture

### Pipeline Flow

The system follows a linear transformation pipeline:

```
PBS file (scenario definition with button metadata)
    ↓ [dlr] Extract dealer code
dlr file (dealer language constraints)
    ↓ [pbn] Generate hands via dealer (500 per scenario)
pbn file (Portable Bridge Notation)
    ↓ [rotate] Create 4-player rotations
pbn-rotated & lin-rotated files
    ↓ [bba] Analyze bidding with BBA
bba file (with bidding analysis)
    ↓ [filter] Filter by auction patterns
bba-filtered & bba-filtered-out files
    ↓ [filterStats] Count statistics
bba-summary (hand counts)
    ↓ [biddingSheet] Generate PDFs
bidding-sheets (final output)
```

### Cross-Platform Architecture

The system bridges Mac and Windows environments:

- **Mac**: Python orchestrator, native dealer tool, wkhtmltopdf for PDFs
- **Windows VM**: Windows-only tools (dealer.exe, BBA.exe/bba-cli, Filter.js, SetDealerMulti.js)
- **Communication**: SSH with UNC path mapping, file-based queuing for GUI apps

Drive mappings (Mac → Windows):
- `G:` → GitHub folder (parent of project)
- `P:` → Project root
- `S:` → BCScript folder

### VS Code Extension Architecture

Located in `vs-code/src/`:

- **Extension lifecycle**: [extension.ts](vs-code/src/extension.ts) - Command registration and activation
- **Tree views**: [buttonPanelProvider.ts](vs-code/src/buttonPanelProvider.ts) - Hierarchical scenario display
- **Webview**: [buttonGridProvider.ts](vs-code/src/buttonGridProvider.ts) - Interactive button grid
- **Current scenario**: [currentScenarioProvider.ts](vs-code/src/currentScenarioProvider.ts) - Focused scenario with artifacts
- **Parser**: [pbsParser.ts](vs-code/src/pbsParser.ts) - PBS file parsing logic
- **Pipeline runner**: [pipelineRunner.ts](vs-code/src/pipelineRunner.ts) - Command execution

Extension provides:
- Syntax highlighting for PBS, DLR, and PBN formats
- Tree view and button grid for scenario navigation
- Pipeline commands accessible via editor title menu
- File watchers for real-time UI updates

### Directory Structure

**Input/Source:**
- `PBS/` - Scenario definitions with button metadata (master files)
- `script/` - Reusable dealer language fragments and macros
- `-PBS.txt` - Master configuration listing all scenarios with section organization

**Generated (Intermediate):**
- `dlr/` - Extracted dealer code
- `pbn/` - Bridge Portable Notation files (~500 hands each)
- `pbn-rotated-for-4-players/` - Rotated PBN for 4-player practice
- `lin-rotated-for-4-players/` - LIN format for BBO
- `bba/` - Bridge Base Archive with bidding analysis
- `bba-filtered/` - Filtered BBA files by auction pattern
- `bba-filtered-out/` - BBA files that were filtered out
- `bba-summary/` - Statistics summaries

**Generated (Final Output):**
- `bidding-sheets/` - PDF bidding sheets for practice

**Source Code:**
- `build-scripts-mac/` - Python pipeline orchestration and operations
- `py/` - Python utilities (oneExtract, oneComment, oneSummary, etc.)
- `vs-code/` - TypeScript VS Code extension
- `js/` - JavaScript for BBO automation

**Configuration:**
- `GIB/` - GIB convention card definitions
- `bbsa/` - Bridge Base Scenario Archive
- `.vscode/` - VS Code workspace settings

### Key Python Modules

Core utilities in `py/`:
- `oneExtract.py` - PBS → DLR extraction
- `oneComment.py` - Adds analysis comments to PBN
- `oneSummary.py` - Generates BBA summaries
- `handPatterns.py` - Hand pattern analysis
- `getBBA.py` - BBA file processing

Pipeline operations in `build-scripts-mac/operations/`:
- Modular operation functions registered in `OPERATIONS` dict
- Each operation is independent and re-runnable
- Operations use config.py for paths and settings

### Data Formats

1. **PBS (Practice Bidding Scenario)**: Custom format combining dealer constraints with button metadata for BBO integration
2. **DLR (Dealer)**: Dealer language for hand generation constraints - a DSL for expressing bridge hand requirements
3. **PBN (Portable Bridge Notation)**: Standard bridge hand format, ~160-170KB per file (~500 hands)
4. **BBA (Bridge Base Archive)**: PBN with bidding analysis, ~300-340KB per file
5. **LIN (BBO format)**: Rotated variant for 4-player practice on BBO

### Configuration System

Central configuration in [build-scripts-mac/config.py](build-scripts-mac/config.py):
- SSH host/user for Windows VM
- Drive mappings (P:, S: drives with UNC paths)
- Tool paths (dealer, bba-cli, wkhtmltopdf)
- Default convention cards: `21GF-DEFAULT`, `21GF-GIB`
- Dealer parameters: seed=5, generate=300000000, produce=500
- Pipeline operations order

## Development Practices

### Working with PBS Files

- PBS files live in the `PBS/` directory and are the master source
- Each PBS file defines a bidding scenario with:
  - Dealer language code for hand generation constraints
  - Button metadata for BBO integration
  - Optional filtering rules for auction patterns
- The `-PBS.txt` file lists all scenarios and their organization
- When creating new scenarios, follow the existing PBS format structure
- **Wide commas in scenario chat**: In the `Button,` section, the chat text content (the descriptive text after the button name) must use wide commas (，) instead of regular commas (,). The structural commas used as PBS syntax delimiters remain as regular commas. When editing PBS files, automatically replace any regular commas in the chat text with wide commas.

### Working with the Pipeline

- Operations are composable and can be run independently
- Each operation reads from its input folder and writes to its output folder
- The pipeline can be resumed from any operation using the "+" suffix (e.g., "bba+" runs from bba to end)
- Always test pipeline changes on a single scenario before running on all scenarios
- File-based queueing is used for GUI tools (BBA.exe) that can't run headless

### Working with the VS Code Extension

- The extension auto-activates when the workspace contains `PBS` folder or `-PBS.txt` file
- Tree views and button grid dynamically update based on file changes
- Commands are registered in [package.json](vs-code/package.json) with menu contributions
- The extension provides context-aware pipeline commands in the editor title bar
- When modifying the extension, use `npm run watch` for continuous compilation

### Cross-Platform Considerations

- Mac is the primary development platform; Windows VM handles Windows-only tools
- SSH runner handles drive mapping and UNC path conversion automatically
- Test Windows tool execution when modifying pipeline operations
- UNC paths must be used for SSH execution (mapped drives don't persist in SSH sessions)

### File Naming Conventions

- PBS files use names like `Smolen` or `Weak_2_Bids`
- Generated files maintain the same base name with different extensions
- Scenario names are used as keys throughout the system
- Avoid spaces in scenario names; use underscores instead

## BBO Integration

The system integrates with Bridge Base Online through:

1. **BBOalert Framework**: `-PBS.txt` file contains BBOalert code to import scenarios
2. **JavaScript Automation**: Scripts in `js/` automate BBO table setup and deal import
3. **Button Grid**: Each scenario becomes a clickable button that imports dealer code to BBO
4. **Deal Source**: Dealer code is automatically set in BBO's "Deal source/Advanced" section
5. **Practice Tables**: Scripts can automatically create bidding or teaching tables with proper settings

Key JavaScript automation functions:
- `setBiddingTable` - Creates and configures a bidding practice table
- `setTeachingTable` - Creates and configures a teaching table
- `setDealerCode` - Imports dealer constraints to BBO
- `displayHCP` - Shows high card points for visible hands

## Key Architecture Decisions

1. **Pipeline as Code**: Operations are Python functions, not configuration files
2. **File-Based Processing**: Each stage produces files consumed by the next stage
3. **Multi-Target Support**: Supports both Mac native dealer and Windows dealer.exe
4. **IDE Integration First**: VS Code extension is the primary UI; CLI is secondary
5. **Modular Operations**: Each pipeline stage is independent and re-runnable
6. **Portable Configuration**: Environment variables instead of hardcoded paths
7. **Cross-Platform Bridge**: SSH and UNC paths enable Mac-Windows workflow

## Project Context

This project is maintained by an 84-year-old bridge enthusiast focused on bridge education without commercial intent. The goal is broad accessibility for bridge players to practice infrequent bidding scenarios. The system bridges multiple tools (dealer, BBA, BBO), operating systems (Mac/Windows), and formats into a cohesive learning platform.
