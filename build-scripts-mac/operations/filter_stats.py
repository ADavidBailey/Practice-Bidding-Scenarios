"""
Filter stats operation: Count hands in filtered files.
This is a Mac-native operation (replaces CountPattern.ps1).
"""
import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS


def count_pattern(file_path: str, pattern: str = r"\[Board") -> int:
    """
    Count occurrences of a pattern in a file.

    Args:
        file_path: Path to the file
        pattern: Regex pattern to count

    Returns:
        Number of matches
    """
    if not os.path.exists(file_path):
        return 0

    regex = re.compile(pattern)
    count = 0

    with open(file_path, "r") as f:
        for line in f:
            if regex.search(line):
                count += 1

    return count


def run_filter_stats(scenario: str, verbose: bool = True) -> bool:
    """
    Count hands in filtered files and print statistics.

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True (always succeeds)
    """
    if verbose:
        print(f"--------- Filter stats for {scenario}")

    filtered_path = os.path.join(FOLDERS["bba_filtered"], f"{scenario}.pbn")
    filtered_out_path = os.path.join(FOLDERS["bba_filtered_out"], f"{scenario}.pbn")

    filtered_count = count_pattern(filtered_path)
    filtered_out_count = count_pattern(filtered_out_path)
    total = filtered_count + filtered_out_count

    if verbose:
        print(f"  Filtered (matching):     {filtered_count:4d} hands")
        print(f"  Filtered out (inverse):  {filtered_out_count:4d} hands")
        print(f"  Total:                   {total:4d} hands")

        if total > 0:
            pct = (filtered_count / total) * 100
            print(f"  Match rate:              {pct:.1f}%")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing filter stats for scenario: {scenario}\n")
    run_filter_stats(scenario)
