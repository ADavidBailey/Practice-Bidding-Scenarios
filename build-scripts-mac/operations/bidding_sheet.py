"""
Bidding sheet operation: Generate bidding sheets from filtered files.
Uses SetDealerMulti.js, BiddingSheets.wsf, and wkhtmltopdf on Windows via SSH.
"""
import os
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, WINDOWS_TOOLS
from ssh_runner import run_windows_command, mac_to_windows_path


def run_bidding_sheet(scenario: str, verbose: bool = True) -> bool:
    """
    Generate bidding sheets from filtered BBA file.

    bba-filtered/{scenario}.pbn -> bidding-sheets/{scenario}.pbn
                                -> bidding-sheets/{scenario} Bidding Sheets.html
                                -> bidding-sheets/{scenario} Bidding Sheets.pdf

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Bidding sheets for {scenario}")

    # Check that filtered file exists
    filtered_path = os.path.join(FOLDERS["bba_filtered"], f"{scenario}.pbn")
    if not os.path.exists(filtered_path):
        print(f"Error: Filtered file not found: {filtered_path}")
        return False

    # Windows paths
    win_filtered = mac_to_windows_path(filtered_path)
    win_sheets_dir = mac_to_windows_path(FOLDERS["bidding_sheets"])

    # Step 1: Rotate for N/S only
    # cscript /nologo S:\SetDealerMulti.js {input}.pbn NS North
    if verbose:
        print(f"  Rotating for N/S...")

    cmd1 = f'cscript /nologo {WINDOWS_TOOLS["set_dealer_multi_js"]} {win_filtered} NS North'

    try:
        returncode, stdout, stderr = run_windows_command(cmd1, verbose=verbose)
        if returncode != 0:
            print(f"Error: SetDealerMulti.js failed")
            return False
    except Exception as e:
        print(f"Error running SetDealerMulti.js: {e}")
        return False

    # Move the rotated file to bidding-sheets folder
    # SetDealerMulti.js creates files with " - NS" suffix (spaces around dash)
    ns_pbn = os.path.join(FOLDERS["bba_filtered"], f"{scenario} - NS.pbn")
    dest_pbn = os.path.join(FOLDERS["bidding_sheets"], f"{scenario}.pbn")

    if os.path.exists(ns_pbn):
        shutil.move(ns_pbn, dest_pbn)
    else:
        print(f"Warning: Rotated file not found: {ns_pbn}")

    # Step 2: Create bidding sheets HTML
    if verbose:
        print(f"  Generating HTML bidding sheets...")

    win_dest_pbn = mac_to_windows_path(dest_pbn)
    cmd2 = f'cscript /nologo {WINDOWS_TOOLS["bidding_sheets_wsf"]} {win_dest_pbn}'

    try:
        returncode, stdout, stderr = run_windows_command(cmd2, verbose=verbose)
        if returncode != 0:
            print(f"Error: BiddingSheets.wsf failed")
            if stderr:
                print(stderr)
            return False
    except Exception as e:
        print(f"Error running BiddingSheets.wsf: {e}")
        return False

    # Step 3: Convert HTML to PDF using wkhtmltopdf on Windows
    if verbose:
        print(f"  Converting to PDF...")

    html_path = os.path.join(FOLDERS["bidding_sheets"], f"{scenario} Bidding Sheets.html")
    pdf_path = os.path.join(FOLDERS["bidding_sheets"], f"{scenario} Bidding Sheets.pdf")

    if not os.path.exists(html_path):
        print(f"Warning: HTML file not found: {html_path}")
        return False

    win_html = mac_to_windows_path(html_path)
    win_pdf = mac_to_windows_path(pdf_path)

    # Use wkhtmltopdf on Windows via SSH
    cmd3 = f'{WINDOWS_TOOLS["wkhtmltopdf"]} --page-size Letter --quiet --disable-smart-shrinking --print-media-type "{win_html}" "{win_pdf}"'

    try:
        returncode, stdout, stderr = run_windows_command(cmd3, verbose=verbose)
        if returncode != 0:
            print(f"Error: wkhtmltopdf failed")
            if stderr:
                print(stderr)
            return False
    except Exception as e:
        print(f"Error running wkhtmltopdf: {e}")
        return False

    if verbose:
        print(f"  Created: {pdf_path}")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing bidding sheet operation with scenario: {scenario}\n")
    success = run_bidding_sheet(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
