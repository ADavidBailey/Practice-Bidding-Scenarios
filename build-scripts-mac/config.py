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
WINDOWS_SSH_HOST = os.environ.get("WINDOWS_HOST")
WINDOWS_SSH_USER = os.environ.get("WINDOWS_USER")

if not WINDOWS_SSH_HOST or not WINDOWS_SSH_USER:
    import sys
    print("Error: Missing required environment variables.")
    print("Add these to your ~/.zshrc:")
    print('  export WINDOWS_HOST="your-windows-ip"')
    print('  export WINDOWS_USER="your-windows-username"')
    print("Then run: source ~/.zshrc")
    sys.exit(1)

# Drive mappings: Mac path -> (Windows drive letter, UNC path)
# UNC paths are needed because SSH sessions don't inherit mapped drives
DRIVE_MAPPINGS = {
    # P: drive maps to the project root
    PROJECT_ROOT: ("P:", r"\\Mac\Home\Developer\GitHub\Practice-Bidding-Scenarios"),
    # S: drive maps to BridgeComposer scripts folder
    os.path.expanduser("~/Documents/BCScript/2024-11-13"): ("S:", r"\\Mac\Home\Documents\BCScript\2024-11-13"),
}

# Folder structure within the project
FOLDERS = {
    "pbs": os.path.join(PROJECT_ROOT, "PBS"),
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
    "dealer": "/Applications/dealer3",  # Mac version of dealer
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
    "dlr",
    "pbn",
    "rotate",
    "bba",
    "title",
    "filter",
    "filterStats",
    "biddingSheet",
]
