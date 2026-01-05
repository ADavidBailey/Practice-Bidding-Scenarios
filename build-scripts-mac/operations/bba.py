"""
BBA operation: Generate BBA file from PBN using BBA.exe (Windows).
Uses a watch folder approach since BBA.exe is a GUI app that can't run over SSH.
Then run oneSummary.py locally to create summary.
"""
import os
import subprocess
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS, DEFAULT_CC2, PROJECT_ROOT, WINDOWS_SSH_HOST, WINDOWS_SSH_USER
from utils.properties import get_convention_card

# BBA queue folder for watch-folder approach
BBA_QUEUE = os.path.join(PROJECT_ROOT, "bba-queue")

# Timeouts
WATCHER_TIMEOUT = 5   # seconds to wait for .starting file before trying to start watcher
BBA_TIMEOUT = 120     # seconds to wait for .done file (BBA completion)


def start_bba_watcher(verbose: bool = True) -> bool:
    """
    Start the BBA watcher on Windows via SSH.
    Uses Start-Process to launch it detached so SSH can return immediately.

    Returns:
        True if command was sent successfully
    """
    if verbose:
        print("  Starting BBA watcher on Windows...")

    ssh_cmd = [
        "ssh",
        f"{WINDOWS_SSH_USER}@{WINDOWS_SSH_HOST}",
        "powershell -Command \"Start-Process powershell -ArgumentList '-WindowStyle Minimized -File P:\\build-scripts\\BBAWatcher.ps1'\""
    ]

    try:
        subprocess.run(ssh_cmd, capture_output=True, timeout=10)
        # Give watcher a moment to start up
        time.sleep(2)
        return True
    except Exception as e:
        print(f"  Warning: Could not start watcher: {e}")
        return False


def run_bba(scenario: str, verbose: bool = True) -> bool:
    """
    Generate BBA file from PBN file using BBA.exe on Windows.

    Uses watch folder approach:
    1. Write .request file with BBA arguments
    2. Wait for .starting file (confirms watcher is running)
    3. Wait for .done file (confirms BBA completed)

    pbn/{scenario}.pbn -> bba/{scenario}.pbn

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- BBA.exe: Creating bba/{scenario}.pbn from pbn/{scenario}.pbn")

    # Check that PBN file exists
    pbn_path = os.path.join(FOLDERS["pbn"], f"{scenario}.pbn")
    if not os.path.exists(pbn_path):
        print(f"Error: PBN file not found: {pbn_path}")
        return False

    # Get convention card from DLR properties
    cc1 = get_convention_card(scenario)
    cc2 = DEFAULT_CC2

    if verbose:
        print(f"  Convention cards: {cc1} vs {cc2}")

    # First delete existing output if present
    bba_output = os.path.join(FOLDERS["bba"], f"{scenario}.pbn")
    if os.path.exists(bba_output):
        os.remove(bba_output)

    # Build request content: scenario,cc1,cc2
    # The watcher constructs the full BBA command from these parameters
    request_content = f"{scenario},{cc1},{cc2}"

    # Ensure queue folder exists
    os.makedirs(BBA_QUEUE, exist_ok=True)

    # File paths for queue protocol
    request_file = os.path.join(BBA_QUEUE, f"{scenario}.request")
    starting_file = os.path.join(BBA_QUEUE, f"{scenario}.starting")
    done_file = os.path.join(BBA_QUEUE, f"{scenario}.done")

    # Clean up any leftover files from previous runs
    for f in [request_file, starting_file, done_file]:
        if os.path.exists(f):
            os.remove(f)

    # Write the request file
    if verbose:
        print(f"  Submitting BBA request...")
    with open(request_file, 'w') as f:
        f.write(request_content)

    # Wait for .starting file (confirms watcher is running)
    if verbose:
        print(f"  Waiting for BBA watcher...")
    start_time = time.time()
    watcher_started = False
    while not os.path.exists(starting_file):
        if time.time() - start_time > WATCHER_TIMEOUT:
            if not watcher_started:
                # Try to start the watcher automatically
                start_bba_watcher(verbose)
                watcher_started = True
                start_time = time.time()  # Reset timeout
            else:
                # Already tried to start watcher, give up
                print(f"Error: BBA watcher not responding.")
                print(f"  Please ensure Windows is logged in.")
                # Clean up request file
                if os.path.exists(request_file):
                    os.remove(request_file)
                return False
        time.sleep(0.5)

    # Wait for .done file (confirms BBA completed)
    if verbose:
        print(f"  BBA is running...")
    start_time = time.time()
    while not os.path.exists(done_file):
        if time.time() - start_time > BBA_TIMEOUT:
            print(f"Error: BBA.exe timed out after {BBA_TIMEOUT} seconds")
            return False
        time.sleep(1)

    # Read the result (handle potential BOM/encoding issues)
    with open(done_file, 'rb') as f:
        result_bytes = f.read()
    # Decode, strip BOM and whitespace
    result = result_bytes.decode('utf-8-sig').strip()

    # Clean up done file
    os.remove(done_file)

    if not result.startswith("OK"):
        print(f"Error: {result}")
        return False

    if verbose:
        print(f"  BBA completed successfully")

    # Verify BBA output was created
    if not os.path.exists(bba_output):
        print(f"Error: BBA output was not created: {bba_output}")
        return False

    # Step 2: Run oneSummary.py locally
    if verbose:
        print(f"--------- oneSummary.py: Creating bba-summary/{scenario}.txt")

    py_dir = FOLDERS["py"]
    summary_script = os.path.join(py_dir, "oneSummary.py")

    if not os.path.exists(summary_script):
        print(f"Error: oneSummary.py not found: {summary_script}")
        return False

    try:
        result = subprocess.run(
            [MAC_TOOLS["python"], summary_script, "--scenario", scenario],
            cwd=py_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        if verbose and result.stdout:
            print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Error running oneSummary.py: {e}")
        if e.stderr:
            print(e.stderr)
        # Don't fail the whole operation if summary fails
        print("  (continuing despite summary error)")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing BBA operation with scenario: {scenario}\n")
    success = run_bba(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
