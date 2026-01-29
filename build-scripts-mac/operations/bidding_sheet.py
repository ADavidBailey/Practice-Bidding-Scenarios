"""
Bidding sheet operation: Generate bidding sheets from filtered files.
Uses bridge-wrangler rotate-deals and to-pdf commands.
"""
import os
import shutil
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS


def run_bidding_sheet(scenario: str, verbose: bool = True) -> bool:
    """
    Generate bidding sheets from filtered BBA file.

    bba-filtered/{scenario}.pbn -> bidding-sheets/{scenario}.pbn
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

    bridge_wrangler = MAC_TOOLS["bridge_wrangler"]

    # Step 1: Rotate for N/S only
    # bridge-wrangler rotate-deals -i input.pbn -p NS -o output.pbn
    dest_pbn = os.path.join(FOLDERS["bidding_sheets"], f"{scenario}.pbn")

    if verbose:
        print(f"  Rotating for N/S...")

    cmd1 = [
        bridge_wrangler, "rotate-deals",
        "-i", filtered_path,
        "-p", "NS",
        "-o", dest_pbn
    ]

    try:
        result = subprocess.run(cmd1, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: bridge-wrangler rotate-deals failed")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running bridge-wrangler rotate-deals: {e}")
        return False

    # Step 2: Generate PDF bidding sheets
    # bridge-wrangler to-pdf -i input.pbn -o output.pdf -l bidding-sheets
    if verbose:
        print(f"  Generating PDF bidding sheets...")

    pdf_path = os.path.join(FOLDERS["bidding_sheets"], f"{scenario} Bidding Sheets.pdf")

    cmd2 = [
        bridge_wrangler, "to-pdf",
        "-i", dest_pbn,
        "-o", pdf_path,
        "-l", "bidding-sheets"
    ]

    try:
        result = subprocess.run(cmd2, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: bridge-wrangler to-pdf failed")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running bridge-wrangler to-pdf: {e}")
        return False

    if verbose:
        print(f"  Created: {pdf_path}")

    # Clean up leftover .html file from old Windows build process
    html_path = os.path.join(FOLDERS["bidding_sheets"], f"{scenario} Bidding Sheets.html")
    if os.path.exists(html_path):
        os.remove(html_path)
        if verbose:
            print(f"  Removed leftover: {html_path}")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing bidding sheet operation with scenario: {scenario}\n")
    success = run_bidding_sheet(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
