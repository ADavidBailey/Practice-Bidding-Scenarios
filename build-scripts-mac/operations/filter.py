"""
Filter operation: Filter BBA file based on auction patterns.
Uses Filter.js on Windows via SSH.
"""
import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, WINDOWS_TOOLS
from ssh_runner import run_windows_command, mac_to_windows_path
from utils.properties import get_auction_filter


def normalize_filter_newlines(filter_expr: str) -> str:
    """
    Normalize newline escapes in filter expression.
    Replace \\n and \n with \r?\n for regex matching.
    """
    # Replace \\n with \n first, then \n with \r?\n
    result = filter_expr.replace("\\\\n", "\\n")
    result = result.replace("\\n", "\\r?\\n")
    return result


def run_filter(scenario: str, verbose: bool = True) -> bool:
    """
    Filter BBA file based on auction patterns.

    bba/{scenario}.pbn -> bba-filtered/{scenario}.pbn
                       -> bba-filtered-out/{scenario}.pbn

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Filter.js: Filtering bba/{scenario}.pbn")

    # Check that BBA file exists
    bba_path = os.path.join(FOLDERS["bba"], f"{scenario}.pbn")
    if not os.path.exists(bba_path):
        print(f"Error: BBA file not found: {bba_path}")
        return False

    # Get auction filter from DLR properties
    filter_expr = get_auction_filter(scenario)

    if not filter_expr:
        print(f"  {scenario} doesn't have a filter expression, skipping")
        return True  # Not an error, just nothing to do

    if verbose:
        print(f"  Filter: {filter_expr}")

    # Normalize newlines in filter expression
    filter_expr = normalize_filter_newlines(filter_expr)

    # Build Windows paths
    win_input = mac_to_windows_path(bba_path)
    win_output_filtered = mac_to_windows_path(os.path.join(FOLDERS["bba_filtered"], f"{scenario}.pbn"))
    win_output_inverse = mac_to_windows_path(os.path.join(FOLDERS["bba_filtered_out"], f"{scenario}.pbn"))

    # Step 1: Filter matching hands
    # cscript /nologo S:\Filter.js {input}.pbn {filter} {output}.pbn --PDF /noui
    cmd1 = f'cscript /nologo {WINDOWS_TOOLS["filter_js"]} {win_input} "{filter_expr}" {win_output_filtered} --PDF /noui'

    try:
        returncode, stdout, stderr = run_windows_command(cmd1, verbose=verbose)
        if returncode != 0:
            print(f"Error: Filter.js failed")
            if stderr:
                print(stderr)
            return False
    except Exception as e:
        print(f"Error running Filter.js: {e}")
        return False

    # Step 2: Filter non-matching hands (inverse)
    cmd2 = f'cscript /nologo {WINDOWS_TOOLS["filter_js"]} {win_input} "{filter_expr}" {win_output_inverse} --INVERSE --PDF /noui'

    try:
        returncode, stdout, stderr = run_windows_command(cmd2, verbose=verbose)
        if returncode != 0:
            print(f"Error: Filter.js (inverse) failed")
            if stderr:
                print(stderr)
            return False
    except Exception as e:
        print(f"Error running Filter.js: {e}")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing filter operation with scenario: {scenario}\n")
    success = run_filter(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
