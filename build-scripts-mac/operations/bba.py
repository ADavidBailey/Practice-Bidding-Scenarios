"""
BBA operation: Generate BBA file from PBN using BBA on Windows.
Supports two modes:
  - CLI mode (default): Uses bba-cli.exe via SSH directly
  - GUI mode: Uses BBA.exe with a watch folder approach (legacy)
Then run oneSummary.py locally to create summary.
"""
import os
import subprocess
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS, DEFAULT_CC2, PROJECT_ROOT
from ssh_runner import run_windows_command, mac_to_windows_path
from utils.properties import get_convention_card

# Set to True to use legacy GUI-based BBA.exe with watcher, False for CLI mode
USE_GUI_MODE = False

# BBA-CLI path on Windows
BBA_CLI_PATH = r"C:\BBA-CLI\bba-cli"

# BBA queue folder for watch-folder approach (GUI mode only)
BBA_QUEUE = os.path.join(PROJECT_ROOT, "bba-queue")

# Timeouts
WATCHER_TIMEOUT = 5   # seconds to wait for .starting file before trying to start watcher
BBA_TIMEOUT = 300     # seconds to wait for BBA completion (increased for CLI mode)


def run_bba_cli(scenario: str, verbose: bool = True) -> bool:
    """
    Generate BBA file from PBN file using bba-cli.exe on Windows via SSH.

    pbn/{scenario}.pbn -> bba/{scenario}.pbn

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- bba-cli: Creating bba/{scenario}.pbn from pbn/{scenario}.pbn")

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

    # Build the bba-cli command using path conversion
    input_file = mac_to_windows_path(os.path.join(FOLDERS["pbn"], f"{scenario}.pbn"))
    output_file = mac_to_windows_path(os.path.join(FOLDERS["bba"], f"{scenario}.pbn"))
    cc1_file = mac_to_windows_path(os.path.join(FOLDERS["bbsa"], f"{cc1}.bbsa"))
    cc2_file = mac_to_windows_path(os.path.join(FOLDERS["bbsa"], f"{cc2}.bbsa"))

    bba_cmd = f'{BBA_CLI_PATH} --input "{input_file}" --output "{output_file}" --ns-conventions "{cc1_file}" --ew-conventions "{cc2_file}"'

    if verbose:
        print(f"  Running: {bba_cmd}")

    # Run via SSH
    try:
        start_time = time.time()
        returncode, stdout, stderr = run_windows_command(bba_cmd, timeout=BBA_TIMEOUT, verbose=False)
        elapsed = time.time() - start_time

        if returncode != 0:
            print(f"Error: bba-cli failed with exit code {returncode}")
            if stderr:
                print(f"  {stderr}")
            return False

        if verbose:
            print(f"  BBA completed successfully in {int(elapsed)}s")
            if stdout:
                print(f"  {stdout.strip()}")

    except TimeoutError:
        print(f"Error: bba-cli timed out after {BBA_TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"Error running bba-cli: {e}")
        return False

    # Verify BBA output was created
    if not os.path.exists(bba_output):
        print(f"Error: BBA output was not created: {bba_output}")
        return False

    # Run oneSummary.py locally
    return run_summary(scenario, verbose)


def start_bba_watcher(verbose: bool = True) -> bool:
    """
    Start the BBA watcher on Windows via SSH.
    Uses scheduled task to run in the user's interactive session.

    Returns:
        True if command was sent successfully
    """
    if verbose:
        print("  Starting BBA watcher on Windows...")

    # Use scheduled task to run in the user's interactive session
    watcher_script = mac_to_windows_path(os.path.join(PROJECT_ROOT, "build-scripts", "BBAWatcher.ps1"))
    schtasks_cmd = f'schtasks /Create /TN BBAWatcher /TR "powershell -ExecutionPolicy Bypass -File {watcher_script}" /SC ONCE /ST 00:00 /F && schtasks /Run /TN BBAWatcher'

    try:
        run_windows_command(schtasks_cmd, timeout=10, verbose=False, check=False)
        # Give watcher a moment to start up
        time.sleep(2)
        return True
    except Exception as e:
        print(f"  Warning: Could not start watcher: {e}")
        return False


def run_bba_gui(scenario: str, verbose: bool = True) -> bool:
    """
    Generate BBA file from PBN file using BBA.exe on Windows (GUI mode).

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

    # Run oneSummary.py locally
    return run_summary(scenario, verbose)


def run_summary(scenario: str, verbose: bool = True) -> bool:
    """
    Run oneSummary.py to create the summary file.

    Args:
        scenario: Scenario name
        verbose: Whether to print progress

    Returns:
        True if successful (or if summary fails but BBA succeeded)
    """
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


def run_bba(scenario: str, verbose: bool = True) -> bool:
    """
    Generate BBA file from PBN file.

    Dispatches to either CLI mode or GUI mode based on USE_GUI_MODE flag.

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if USE_GUI_MODE:
        return run_bba_gui(scenario, verbose)
    else:
        return run_bba_cli(scenario, verbose)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing BBA operation with scenario: {scenario}\n")
    print(f"Mode: {'GUI (BBA.exe watcher)' if USE_GUI_MODE else 'CLI (bba-cli)'}\n")
    success = run_bba(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
