# Mac Build Pipeline for Practice-Bidding-Scenarios

This folder contains a Python-based build pipeline for running on Mac, using SSH to execute Windows-only tools on a Parallels VM.

## Quick Start

```bash
cd build-scripts-mac

# Run all operations on a single scenario
python3 pbs-pipeline-mac.py Smolen "*"

# Run specific operations
python3 pbs-pipeline-mac.py Smolen dlr,pbn,bba

# Run from an operation through the end
python3 pbs-pipeline-mac.py Smolen "bba+"

# Run all scenarios
python3 pbs-pipeline-mac.py "*" "*"
```

## Prerequisites

### Mac
- Python 3 with `requests` module: `pip3 install requests --user --break-system-packages`
- wkhtmltopdf (for PDF generation): `brew install wkhtmltopdf`
- SSH access to Windows VM

### Windows VM
- OpenSSH Server enabled
- P: drive mapped to `\\Mac\Home\Developer\GitHub\Practice-Bidding-Scenarios`
- S: drive mapped to `\\Mac\Home\Documents\BCScript\2024-11-13` (BridgeComposer scripts)
- BBA.exe installed and in PATH (C:\BBA\)
- BBAWatcher.ps1 running (required for BBA operation)

### Starting the BBA Watcher (Windows)
BBA.exe is a GUI application that can't run over SSH. A watcher script handles BBA requests:

```powershell
# Run in PowerShell on Windows
powershell -File P:\build-scripts\BBAWatcher.ps1
```

To run at Windows startup, create a shortcut to the script in `shell:startup`.

## Operations

| Operation | Description | Runs On |
|-----------|-------------|---------|
| `dlr` | Extract dealer code from PBS file | Mac (py/oneExtract.py) |
| `pbn` | Generate PBN from DLR | Mac (dealer) or Windows (dealer.exe via SSH) |
| `rotate` | Create rotated PBN/LIN for 4-player practice | Windows (SetDealerMulti.js via SSH) |
| `bba` | Generate BBA with bidding analysis | Windows (BBA.exe via watcher) |
| `title` | Set title (skipped) | - |
| `filter` | Filter BBA by auction patterns | Windows (Filter.js via SSH) |
| `filterStats` | Count hands in filtered files | Mac (native Python) |
| `biddingSheet` | Generate bidding sheet PDFs | Windows + Mac |

## File Flow

```
PBS/{scenario}
    ↓ dlr (oneExtract.py)
dlr/{scenario}.dlr
    ↓ pbn (dealer.exe)
pbn/{scenario}.pbn
    ↓ rotate (SetDealerMulti.js)
pbn-rotated-for-4-players/{scenario}.pbn
lin-rotated-for-4-players/{scenario}.lin
    ↓ bba (BBA.exe)
bba/{scenario}.pbn
bba-summary/{scenario}.txt
    ↓ filter (Filter.js)
bba-filtered/{scenario}.pbn
bba-filtered-out/{scenario}.pbn
    ↓ biddingSheet (SetDealerMulti.js + wkhtmltopdf)
bidding-sheets/{scenario}.pbn
bidding-sheets/{scenario} Bidding Sheets.pdf
```

## Configuration

### Environment Variables (required)

Add these to your `~/.zshrc`:

```bash
# Windows VM connection (required)
export WINDOWS_HOST="your-windows-ip"    # e.g., "10.211.55.5"
export WINDOWS_USER="your-username"       # Your Windows username
```

Then run `source ~/.zshrc` to apply.

### Environment Variables (optional)

```bash
# Where to run dealer: "mac" (default) or "windows"
export PBS_DEALER_PLATFORM="mac"
```

By default, the `pbn` operation runs `dealer` locally on Mac (`/Applications/dealer`). Set to `"windows"` to run `dealer.exe` on the Windows VM via SSH instead.

### config.py (shared settings)

Edit `config.py` to change:
- `DRIVE_MAPPINGS` - Mac path to Windows drive letter mappings
- `DEFAULT_CC1` / `DEFAULT_CC2` - Default convention cards for BBA

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         MAC                                  │
│  pbs-pipeline-mac.py (orchestrator)                         │
│  ├── operations/dlr.py      → py/oneExtract.py (local)     │
│  ├── operations/pbn.py      → dealer (local or SSH)        │
│  ├── operations/rotate.py   → SetDealerMulti.js (SSH)      │
│  ├── operations/bba.py      → BBA.exe (via watcher)        │
│  ├── operations/filter.py   → Filter.js (SSH)              │
│  └── operations/bidding_sheet.py → wkhtmltopdf (local)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ SSH / File Queue
┌──────────────────────▼──────────────────────────────────────┐
│                      WINDOWS VM                              │
│  - P:\ and S:\ mapped to Mac folders                        │
│  - dealer.exe, BBA.exe, cscript for .js/.wsf scripts        │
│  - BBAWatcher.ps1 monitors bba-queue/ for requests          │
└─────────────────────────────────────────────────────────────┘
```

## BBA Watcher Protocol

Since BBA.exe requires a GUI session, it uses a file-based queue:

1. Mac writes `bba-queue/{scenario}.request` containing: `scenario,cc1,cc2`
2. Watcher creates `bba-queue/{scenario}.starting` to acknowledge
3. Watcher runs BBA.exe with constructed command
4. Watcher creates `bba-queue/{scenario}.done` with "OK" or error message
5. Watcher cleans up .request and .starting files

## Troubleshooting

### SSH connection fails
```bash
# Test SSH manually (use your Windows IP and username)
ssh $WINDOWS_USER@$WINDOWS_HOST "echo hello"

# If it fails, ensure OpenSSH Server is enabled on Windows
```

### Drive not accessible via SSH
SSH sessions don't inherit mapped drives. The ssh_runner.py automatically runs `net use` commands to map P: and S: before each command.

### BBA watcher not responding
- Ensure Windows is logged in (not just VM running)
- Start the watcher: `powershell -File P:\build-scripts\BBAWatcher.ps1`
- Check for errors in the watcher console

### "No module named 'requests'"
```bash
pip3 install requests --user --break-system-packages
```

## Files

```
build-scripts-mac/
├── pbs-pipeline-mac.py  # Main CLI orchestrator
├── config.py          # Configuration (SSH, paths, tools)
├── ssh_runner.py      # SSH command execution
├── operations/
│   ├── dlr.py         # PBS → DLR
│   ├── pbn.py         # DLR → PBN
│   ├── rotate.py      # PBN rotation
│   ├── bba.py         # PBN → BBA (via watcher)
│   ├── filter.py      # BBA filtering
│   ├── filter_stats.py # Count filtered hands
│   └── bidding_sheet.py # Generate PDFs
└── utils/
    ├── paths.py       # Mac ↔ Windows path conversion
    └── properties.py  # Read properties from .dlr files
```
