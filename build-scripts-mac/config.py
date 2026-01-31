"""
Configuration for the Mac build pipeline.
"""
import os

# Project root directory (parent of build-scripts-mac)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Windows VM SSH configuration
# Set these environment variables in your ~/.zshrc:
#   export WINDOWS_HOST="your-windows-ip"
#   export WINDOWS_USER="your-windows-username"
#   export PBS_UNC_PREFIX="\\Mac\Home"  (for Parallels) or your VM's UNC prefix
#   export PBS_BCSCRIPT_PATH="~/Documents/BCScript/2024-11-13"  (path to BCScript folder)
WINDOWS_SSH_HOST = os.environ.get("WINDOWS_HOST")
WINDOWS_SSH_USER = os.environ.get("WINDOWS_USER")
UNC_PREFIX = os.environ.get("PBS_UNC_PREFIX")
BCSCRIPT_PATH = os.environ.get("PBS_BCSCRIPT_PATH")

_missing = []
if not WINDOWS_SSH_HOST:
    _missing.append('WINDOWS_HOST')
if not WINDOWS_SSH_USER:
    _missing.append('WINDOWS_USER')
if not UNC_PREFIX:
    _missing.append('PBS_UNC_PREFIX')
if not BCSCRIPT_PATH:
    _missing.append('PBS_BCSCRIPT_PATH')

if _missing:
    import sys
    print(f"Error: Missing required environment variables: {', '.join(_missing)}")
    print("Add these to your ~/.zshrc:")
    print('  export WINDOWS_HOST="your-windows-ip"')
    print('  export WINDOWS_USER="your-windows-username"')
    print('  export PBS_UNC_PREFIX="\\\\Mac\\Home"  # For Parallels; adjust for your VM')
    print('  export PBS_BCSCRIPT_PATH="~/Documents/BCScript/2024-11-13"')
    print("Then run: source ~/.zshrc")
    sys.exit(1)

# Helper to convert Mac path to UNC path
def _mac_to_unc(mac_path: str) -> str:
    """Convert a Mac path to a UNC path using the configured prefix."""
    expanded = os.path.expanduser(mac_path)
    # Remove leading ~ expansion to get path relative to home
    home = os.path.expanduser("~")
    if expanded.startswith(home):
        relative = expanded[len(home):]
        return UNC_PREFIX + relative.replace("/", "\\")
    return expanded.replace("/", "\\")

# Expand BCScript path
_bcscript_expanded = os.path.expanduser(BCSCRIPT_PATH)

# Drive mappings: Mac path -> (Windows drive letter, UNC path)
# UNC paths are needed because SSH sessions don't inherit mapped drives
DRIVE_MAPPINGS = {
    # G: drive maps to GitHub folder (one level above project)
    os.path.dirname(PROJECT_ROOT): ("G:", _mac_to_unc(os.path.dirname(PROJECT_ROOT))),
    # P: drive maps to the project root
    PROJECT_ROOT: ("P:", _mac_to_unc(PROJECT_ROOT)),
    # S: drive maps to BridgeComposer scripts folder
    _bcscript_expanded: ("S:", _mac_to_unc(_bcscript_expanded)),
}

# Folder structure within the project
FOLDERS = {
    "btn": os.path.join(PROJECT_ROOT, "btn"),
    "pbs": os.path.join(PROJECT_ROOT, "PBS"),
    "pbs_test": os.path.join(PROJECT_ROOT, "pbs-test"),
    "dlr": os.path.join(PROJECT_ROOT, "dlr"),
    "pbn": os.path.join(PROJECT_ROOT, "pbn"),
    "pbn_rotated": os.path.join(PROJECT_ROOT, "pbn-rotated-for-4-players"),
    "lin_rotated": os.path.join(PROJECT_ROOT, "lin-rotated-for-4-players"),
    "bba": os.path.join(PROJECT_ROOT, "bba"),
    "bba_summary": os.path.join(PROJECT_ROOT, "bba-summary"),
    "bba_filtered": os.path.join(PROJECT_ROOT, "bba-filtered"),
    "bba_filtered_out": os.path.join(PROJECT_ROOT, "bba-filtered-out"),
    "bidding_sheets": os.path.join(PROJECT_ROOT, "bidding-sheets"),
    "bbsa": os.path.join(PROJECT_ROOT, "bbsa"),
    "py": os.path.join(PROJECT_ROOT, "py"),
}

# Windows tool paths (as seen from Windows)
WINDOWS_TOOLS = {
    "dealer": "P:\\dealer.exe",
    "bba": "BBA.exe",  # Assumes BBA.exe is in Windows PATH
    "cscript": "cscript",
    "filter_js": "S:\\Filter.js",
    "set_dealer_multi_js": "S:\\SetDealerMulti.js",
    "bidding_sheets_wsf": "S:\\BiddingSheets.wsf",
    "wkhtmltopdf": "wkhtmltopdf",  # Assumes wkhtmltopdf is in Windows PATH
}

# Mac tool paths
MAC_TOOLS = {
    "python": "python3",
    "wkhtmltopdf": "/opt/homebrew/bin/wkhtmltopdf",  # Adjust if installed elsewhere
    "dealer": "/Applications/Bridge Utilities/dealer3",  # Mac version of dealer
    "bridge_wrangler": "/Applications/Bridge Utilities/bridge-wrangler",
}

# Where to run dealer: "mac" (default) or "windows"
DEALER_PLATFORM = os.environ.get("PBS_DEALER_PLATFORM", "mac").lower()

# Default convention cards
DEFAULT_CC1 = "21GF-DEFAULT"
DEFAULT_CC2 = "21GF-GIB"

# Dealer parameters
DEALER_SEED = 5
DEALER_GENERATE = 300000000
DEALER_PRODUCE = 500

# Pipeline operations in order
OPERATIONS_ORDER = [
    "pbs",      # Generate PBS from BTN (also generates DLR)
    "pbn",
    "rotate",
    "bba",
    "filter",
    "filterStats",
    "biddingSheet",
]
