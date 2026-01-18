"""
Rotate operation: Create rotated PBN and LIN files for 4-player practice.
Uses SetDealerMulti.js on Windows via SSH.
"""
import os
import shutil
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, WINDOWS_TOOLS
from ssh_runner import run_windows_command, mac_to_windows_path


def run_rotate(scenario: str, verbose: bool = True) -> bool:
    """
    Create rotated PBN and LIN files for 4-player practice.

    pbn/{scenario}.pbn -> pbn-rotated-for-4-players/{scenario}.pbn
                       -> lin-rotated-for-4-players/{scenario}.lin

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- SetDealerMulti.js: Creating rotated files for {scenario}")

    # Check that PBN file exists
    pbn_path = os.path.join(FOLDERS["pbn"], f"{scenario}.pbn")
    if not os.path.exists(pbn_path):
        print(f"Error: PBN file not found: {pbn_path}")
        return False

    # Windows paths
    win_pbn = mac_to_windows_path(pbn_path)
    # Remove .pbn extension for the base path
    win_pbn_base = win_pbn[:-4]

    # Step 1: Create rotated PBN (NESW rotation)
    # cscript S:\SetDealerMulti.js {input}.pbn NESW Dealer /noui
    cmd1 = f'cscript {WINDOWS_TOOLS["set_dealer_multi_js"]} {win_pbn} NESW Dealer /noui'

    try:
        returncode, stdout, stderr = run_windows_command(cmd1, verbose=verbose)
        if returncode != 0:
            print(f"Error: SetDealerMulti.js (PBN) failed")
            return False
    except Exception as e:
        print(f"Error running SetDealerMulti.js: {e}")
        return False

    # Step 2: Create rotated LIN
    # cscript S:\SetDealerMulti.js {input}.pbn NESW Dealer NoPBN LIN /noui
    cmd2 = f'cscript {WINDOWS_TOOLS["set_dealer_multi_js"]} {win_pbn} NESW Dealer NoPBN LIN /noui'

    try:
        returncode, stdout, stderr = run_windows_command(cmd2, verbose=verbose)
        if returncode != 0:
            print(f"Error: SetDealerMulti.js (LIN) failed")
            return False
    except Exception as e:
        print(f"Error running SetDealerMulti.js: {e}")
        return False

    # Step 3: Move the rotated files to the correct folders
    # The script creates files with " - NESW" suffix (space-hyphen-space) in the same folder
    nesw_pbn = os.path.join(FOLDERS["pbn"], f"{scenario} - NESW.pbn")
    nesw_lin = os.path.join(FOLDERS["pbn"], f"{scenario} - NESW.lin")

    # Destination paths
    dest_pbn = os.path.join(FOLDERS["pbn_rotated"], f"{scenario}.pbn")
    dest_lin = os.path.join(FOLDERS["lin_rotated"], f"{scenario}.lin")

    try:
        if os.path.exists(nesw_pbn):
            shutil.move(nesw_pbn, dest_pbn)
            if verbose:
                print(f"  Moved to {dest_pbn}")
        else:
            print(f"Warning: Rotated PBN not found: {nesw_pbn}")

        if os.path.exists(nesw_lin):
            shutil.move(nesw_lin, dest_lin)
            if verbose:
                print(f"  Moved to {dest_lin}")
        else:
            print(f"Warning: Rotated LIN not found: {nesw_lin}")

    except Exception as e:
        print(f"Error moving rotated files: {e}")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing rotate operation with scenario: {scenario}\n")
    success = run_rotate(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
