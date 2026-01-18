"""
PBN operation: Generate PBN file from DLR using dealer (Mac or Windows).
Then run oneComment.py locally to add comments.
"""
import os
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS, WINDOWS_TOOLS, DEALER_SEED, DEALER_GENERATE, DEALER_PRODUCE, DEALER_PLATFORM
from ssh_runner import run_windows_command, mac_to_windows_path


def run_pbn(scenario: str, verbose: bool = True) -> bool:
    """
    Generate PBN file from DLR file using dealer.

    dlr/{scenario}.dlr -> pbn/{scenario}.pbn

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    # Check that DLR file exists
    dlr_path = os.path.join(FOLDERS["dlr"], f"{scenario}.dlr")
    if not os.path.exists(dlr_path):
        print(f"Error: DLR file not found: {dlr_path}")
        return False

    pbn_path = os.path.join(FOLDERS["pbn"], f"{scenario}.pbn")

    if DEALER_PLATFORM == "mac":
        # Step 1: Run dealer locally on Mac
        # Note: dealer3 reads input from stdin, not as a file argument
        if verbose:
            print(f"--------- dealer (Mac): Creating pbn/{scenario}.pbn from dlr/{scenario}.dlr")

        dealer_cmd = [
            MAC_TOOLS["dealer"],
            "-s", str(DEALER_SEED),
            "-g", str(DEALER_GENERATE),
            "-p", str(DEALER_PRODUCE),
            "-m",
            "-v",        # Include stats output at end of file
            "--legacy",  # Match Windows dealer.exe output format
        ]

        if verbose:
            print(f"  [Local] {' '.join(dealer_cmd)} < {dlr_path}")

        try:
            with open(dlr_path, 'r') as infile, open(pbn_path, 'w') as outfile:
                result = subprocess.run(
                    dealer_cmd,
                    stdin=infile,
                    stdout=outfile,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode != 0:
                print(f"Error: dealer failed with exit code {result.returncode}")
                if result.stderr:
                    print(result.stderr)
                return False

        except Exception as e:
            print(f"Error running dealer: {e}")
            return False

    else:
        # Step 1: Run dealer.exe on Windows via SSH
        if verbose:
            print(f"--------- dealer.exe (Windows): Creating pbn/{scenario}.pbn from dlr/{scenario}.dlr")

        # Build Windows paths
        win_dlr = mac_to_windows_path(dlr_path)
        win_pbn = mac_to_windows_path(pbn_path)

        # Build dealer command
        dealer_cmd = (
            f'{WINDOWS_TOOLS["dealer"]} {win_dlr} '
            f'-s {DEALER_SEED} -g {DEALER_GENERATE} -p {DEALER_PRODUCE} -m '
            f'>{win_pbn}'
        )

        try:
            returncode, stdout, stderr = run_windows_command(dealer_cmd, verbose=verbose)

            if returncode != 0:
                print(f"Error: dealer.exe failed with exit code {returncode}")
                if stderr:
                    print(stderr)
                return False

        except Exception as e:
            print(f"Error running dealer.exe: {e}")
            return False

    # Step 2: Run oneComment.py locally to add comments
    if verbose:
        print(f"--------- oneComment.py: Adding comments to pbn/{scenario}.pbn")

    py_dir = FOLDERS["py"]
    comment_script = os.path.join(py_dir, "oneComment.py")

    if not os.path.exists(comment_script):
        print(f"Error: oneComment.py not found: {comment_script}")
        return False

    try:
        result = subprocess.run(
            [MAC_TOOLS["python"], comment_script, "--scenario", scenario],
            cwd=py_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        if verbose and result.stdout:
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Error running oneComment.py: {e}")
        if e.stderr:
            print(e.stderr)
        return False

    # Verify output was created
    pbn_path = os.path.join(FOLDERS["pbn"], f"{scenario}.pbn")
    if os.path.exists(pbn_path):
        return True
    else:
        print(f"Error: PBN file was not created: {pbn_path}")
        return False


if __name__ == "__main__":
    # Test with a scenario
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing PBN operation with scenario: {scenario}\n")
    success = run_pbn(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
