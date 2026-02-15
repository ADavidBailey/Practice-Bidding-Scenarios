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
- Drive mappings are handled automatically via `net use` commands (configured via `PBS_UNC_PREFIX` env var)
- BBA.exe installed and in PATH (C:\BBA\)
- BBAWatcher.ps1 running (required for BBA operation in GUI mode)

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

Add these to your `~/.zshenv` (not `~/.zshrc`) so they're available to non-interactive shells like VSCode:

```bash
# Windows VM connection
export WINDOWS_HOST="your-windows-ip"    # e.g., "10.211.55.5"
export WINDOWS_USER="your-username"       # Your Windows username

# Path mappings for Mac ↔ Windows file access
export PBS_UNC_PREFIX="\\\\Mac\\Home"     # For Parallels; VMware might use "\\\\vmware-host\\Shared Folders"
export PBS_BCSCRIPT_PATH="~/Documents/BCScript/2024-11-13"  # Path to BridgeComposer scripts
```

Restart your terminal or VSCode for the changes to take effect.

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

---

## Full Build Report — 2025-02-14

Full rebuild of all 299 scenarios with `pbn+` operations using dynamic per-scenario seeding (SEED_OFFSET=1).

```
python3 pbs-pipeline-mac.py "*" "pbn+" -q --no-ssh-check
```

### Results

- **261 succeeded**, **38 failed**
- Total PBN generation time: **30m 17s**

### Error Categories

| Category | Count | Details |
|----------|-------|---------|
| No boards after filtering | 28 | BBA auction filter matched 0 boards with new seeds — bidding sheet generation fails |
| Missing BBSA file | 5 | Custom convention cards not found: `21GF-1NTwith4441`, `Gazzilli`, `21GF-Kokish_Relay`, `21GF-MST`, plus a BTN parsing bug in `Minor_Game_Or_Slam` |
| Dealer found 0 hands | 2 | `GIB_1M-P-Resp` and `Misfit6-5` — constraints too tight, 0 qualifying hands in 300M tries |
| Filter regex error | 1 | `After_2_Passes` — uses look-behind regex unsupported by bridge-wrangler |
| Dealer variable error | 1 | `Anything_Goes` — undefined variable `gamble3` |
| Bidding sheet path error | 1 | `Grand_Slam_Invite` — filtered file not found |

### Failed Scenarios

**Missing BBSA file (5):**
`1N_with_Singleton`, `Gazzilli`, `Kokish_Relay`, `Minor_Game_Or_Slam`, `Minor_Suit_Transfer`

**No boards after filtering (28):**
`After_1M_2M`, `After_1x_1N`, `Better_Minor_Lebensohl`, `Forcing_Pass`, `Gerber_By_Responder`, `Maximal_After_Overcall`, `Minor_Suit_Stayman`, `Mitchell_Stayman`, `Opps_Gambling_3N`, `Opps_Multi_2D`, `Opps_Overcall_1NT`, `Power_Double_Unbalanced`, `Preempt_Keycard`, `Responsive_Double`, `Reverse_Flannery`, `Rule_of_16`, `Rule_of_16-15`, `Rule_of_16-16`, `Rule_of_16-17`, `Rule_of_16-18`, `Rule_of_2`, `Snapdragon_Double`, `Soloway_Jump_Shift_Type-1`, `Spiral_Raises_with_3`, `Support_Double`, `Vics_Bal_Resp_to_1m`, `We_Overcall_NT_then_Smolen`, `Weak_NT_10-12`

**Dealer errors (3):**
`GIB_1M-P-Resp` (0 hands produced), `Misfit6-5` (0 hands produced), `Anything_Goes` (undefined variable)

**Other (2):**
`After_2_Passes` (regex), `Grand_Slam_Invite` (missing filtered file)

### Slow PBN Generation (>10s)

| Scenario | PBN time |
|----------|----------|
| Trap_Pass | 2m 19s |
| Trap_Pass_Maybe | 2m 18s |
| Opps_Bal_Unusual_2N | 2m 9s |
| Gerber_By_Opener | 2m 0s |
| GIB_1M-P-Resp | 1m 45s (failed) |
| GIB_Sandwich_NT_BPH | 1m 45s |
| Double_by_Advancer | 1m 40s |
| W2_X_XX | 1m 19s |
| McCabe_after_WJO | 1m 15s |
| Non_Leaping_Michaels_After_2-Bid | 1m 14s |
| Misfit6-5 | 1m 9s (failed) |
| Snapdragon_Double | 46s |
| Trap_Pass_Opener | 29s |
| 1N_5M_and_6m | 28s |
| Double_double | 24s |
| Impossible_2S | 22s |
| Two-Way_Game_Try | 22s |
| Forcing_Pass | 21s |
| Last_Train_Game_Try | 21s |
| Rule_of_16-18 | 18s |
| Grand_Slam_Force | 18s |
| 3N_over_LHO_3x | 16s |
| We_Overcall_NT_then_Smolen | 14s |
| 1m-2N | 12s |
| McCabe_After_Weak_2 | 12s |
| Trap_Pass_Opener_Maybe | 12s |
| Maximal_Double | 12s |
| Jump_Cuebid_Strong | 11s |
| Spear | 11s |
| Last_Train_GT2 | 10s |

### PBN Duration Distribution

| Range | Count |
|-------|-------|
| < 1s | 175 |
| 1-5s | 77 |
| 5-10s | 17 |
| 10-30s | 18 |
| 30s-1m | 1 |
| 1-2m | 8 |
| 2-5m | 3 |

Default `DEALER_GENERATE` is 300,000,000. The slow scenarios have tight constraints (predeals, calm opponents, narrow HCP ranges) that make it hard to find 500 qualifying hands. Options: reduce `generate`, accept fewer hands, loosen constraints, or add per-scenario `generate` overrides in BTN metadata.
