"""
Filter operation: Filter BBA file based on auction patterns.
Uses bridge-wrangler filter command.
"""
import os
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS
from utils.properties import get_auction_filter


def normalize_filter_for_bridge_wrangler(filter_expr: str) -> str:
    """
    Normalize filter expression for bridge-wrangler.

    - Adds (?s) flag to enable dotall mode (. matches newlines)
    - Converts escaped \\n sequences to actual newlines
    - Converts \\r?\\n to just newlines (bridge-wrangler handles line endings)
    - Converts single spaces to \\s+ to match variable whitespace in PBN files
    """
    result = filter_expr

    # Convert escaped newlines to actual newlines
    # Handle both \\n and \n patterns
    result = result.replace("\\r?\\n", "\n")
    result = result.replace("\\n", "\n")

    # Replace single spaces with \s+ to match variable whitespace in PBN files
    # (PBN auctions have multiple spaces between bids like "1D    Pass  1S")
    result = result.replace(" ", r"\s+")

    # Add (?s) flag at the beginning for dotall mode
    if not result.startswith("(?s)"):
        result = "(?s)" + result

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
        print(f"--------- bridge-wrangler filter: Filtering bba/{scenario}.pbn")

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

    # Normalize filter expression for bridge-wrangler
    filter_expr = normalize_filter_for_bridge_wrangler(filter_expr)

    bridge_wrangler = MAC_TOOLS["bridge_wrangler"]
    output_filtered = os.path.join(FOLDERS["bba_filtered"], f"{scenario}.pbn")
    output_inverse = os.path.join(FOLDERS["bba_filtered_out"], f"{scenario}.pbn")

    # Run filter with both matched and not-matched outputs
    # bridge-wrangler filter -i input.pbn -p "pattern" -m matched.pbn -n not-matched.pbn
    cmd = [
        bridge_wrangler, "filter",
        "-i", bba_path,
        "-p", filter_expr,
        "-m", output_filtered,
        "-n", output_inverse
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: bridge-wrangler filter failed")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running bridge-wrangler filter: {e}")
        return False

    if verbose:
        print(f"  Created: {output_filtered}")
        print(f"  Created: {output_inverse}")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing filter operation with scenario: {scenario}\n")
    success = run_filter(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
