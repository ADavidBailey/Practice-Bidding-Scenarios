"""
BBA operation: Generate BBA file from PBN using BBA.
Supports three modes:
  - GUI mode: Uses BBA.exe with a watch folder approach (legacy Windows)
  - CLI mode: Uses bba-cli.exe on Windows via SSH
  - Mac mode: Uses bba-cli-mac natively on Mac
Then run oneSummary.py locally to create summary.

After BBA completes, restores header comments and fixes Event tags
that BBA strips or overwrites.
"""
import os
import re
import subprocess
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS, PROJECT_ROOT
from ssh_runner import run_windows_command, mac_to_windows_path
from utils.properties import get_convention_card_ns, get_convention_card_ew
from operations.title import get_title_from_pbs

# BBA mode: "gui" (legacy BBA.exe watcher), "cli" (bba-cli.exe via SSH), "mac" (bba-cli-mac native)
BBA_MODE = "mac"

# BBA-CLI path on Windows (G: maps to GitHub root)
BBA_CLI_PATH = r"G:\BBA-CLI\dist\epbot-wrapper\bba-cli.exe"

# BBA queue folder for watch-folder approach (GUI mode only)
BBA_QUEUE = os.path.join(PROJECT_ROOT, "bba-queue")

# Timeouts
WATCHER_TIMEOUT = 5   # seconds to wait for .starting file before trying to start watcher
BBA_TIMEOUT = 300     # seconds to wait for BBA completion (increased for CLI mode)


def fix_event_tags(scenario: str, file_path: str, verbose: bool = True) -> bool:
    """
    Fix title metadata in a PBN file with the correct title from PBS.

    BBA overwrites Event tags with Windows paths like "P:\\bba\\scenario".
    This function:
    - Adds/updates %HRTitleEvent header comment (used by pbn-to-pdf)
    - Replaces all [Event "..."] tags with the proper title

    Args:
        scenario: Scenario name
        file_path: Path to the PBN file to fix
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    title = get_title_from_pbs(scenario)

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Update or add %HRTitleEvent in header
        hr_title_line = f'%HRTitleEvent "{title}"\n'
        hr_pattern = re.compile(r'^%HRTitleEvent\s')
        found_hr_title = False
        insert_pos = 0

        for i, line in enumerate(lines):
            if hr_pattern.match(line):
                # Replace existing %HRTitleEvent
                lines[i] = hr_title_line
                found_hr_title = True
                break
            elif line.startswith('%'):
                # Track last header comment position
                insert_pos = i + 1
            elif line.startswith('['):
                # Reached first board, stop looking
                break

        if not found_hr_title:
            # Insert %HRTitleEvent after other header comments
            lines.insert(insert_pos, hr_title_line)

        # Join lines back to content
        content = ''.join(lines)

        # Replace all [Event "..."] tags with the correct title
        pattern = r'\[Event "[^"]*"\]'
        replacement = f'[Event "{title}"]'
        updated_content = re.sub(pattern, replacement, content)

        # Remove all [Date "..."] lines to avoid spurious diffs
        updated_content = re.sub(r'\[Date "[^"]*"\]\n?', '', updated_content)

        with open(file_path, "w") as f:
            f.write(updated_content)

        if verbose:
            count = len(re.findall(pattern, content))
            print(f"  Fixed {count} Event tags with title: {title}")

        return True

    except Exception as e:
        print(f"Error fixing Event tags: {e}")
        return False


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

    # Get convention cards from DLR properties
    cc1 = get_convention_card_ns(scenario)
    cc2 = get_convention_card_ew(scenario)

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

    event_name = scenario.replace("_", " ")
    bba_cmd = f'{BBA_CLI_PATH} --input "{input_file}" --output "{output_file}" --ns-conventions "{cc1_file}" --ew-conventions "{cc2_file}" --event "{event_name}"'

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

    # Fix Event tags with correct title from PBS
    fix_event_tags(scenario, bba_output, verbose)

    # Run oneSummary.py locally
    return run_summary(scenario, verbose)


def run_bba_mac(scenario: str, verbose: bool = True, output_dir: str = None) -> bool:
    """
    Generate BBA file from PBN file using bba-cli-mac natively on Mac.

    pbn/{scenario}.pbn -> bba/{scenario}.pbn (or output_dir/{scenario}.pbn)

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress
        output_dir: Optional override for output directory (for comparison testing)

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- bba-cli-mac: Creating bba/{scenario}.pbn from pbn/{scenario}.pbn")

    bba_cli_mac = MAC_TOOLS.get("bba_cli")
    if not bba_cli_mac or not os.path.exists(bba_cli_mac):
        print(f"Error: bba-cli-mac not found at: {bba_cli_mac}")
        return False

    # Check that PBN file exists
    pbn_path = os.path.join(FOLDERS["pbn"], f"{scenario}.pbn")
    if not os.path.exists(pbn_path):
        print(f"Error: PBN file not found: {pbn_path}")
        return False

    # Get convention cards from DLR properties
    cc1 = get_convention_card_ns(scenario)
    cc2 = get_convention_card_ew(scenario)

    if verbose:
        print(f"  Convention cards: {cc1} vs {cc2}")

    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        bba_output = os.path.join(output_dir, f"{scenario}.pbn")
    else:
        bba_output = os.path.join(FOLDERS["bba"], f"{scenario}.pbn")

    # Delete existing output if present
    if os.path.exists(bba_output):
        os.remove(bba_output)

    # Build convention card paths
    cc1_file = os.path.join(FOLDERS["bbsa"], f"{cc1}.bbsa")
    cc2_file = os.path.join(FOLDERS["bbsa"], f"{cc2}.bbsa")

    cmd = [
        bba_cli_mac,
        "--input", pbn_path,
        "--output", bba_output,
        "--ns-conventions", cc1_file,
        "--ew-conventions", cc2_file,
        "--event", scenario.replace("_", " "),
    ]

    if verbose:
        print(f"  Running: {' '.join(cmd)}")

    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=BBA_TIMEOUT,
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            print(f"Error: bba-cli-mac failed with exit code {result.returncode}")
            if result.stderr:
                print(f"  {result.stderr}")
            return False

        if verbose:
            print(f"  BBA completed successfully in {int(elapsed)}s")
            if result.stdout:
                print(f"  {result.stdout.strip()}")

    except subprocess.TimeoutExpired:
        print(f"Error: bba-cli-mac timed out after {BBA_TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"Error running bba-cli-mac: {e}")
        return False

    # Verify BBA output was created
    if not os.path.exists(bba_output):
        print(f"Error: BBA output was not created: {bba_output}")
        return False

    # Fix Event tags with correct title from PBS
    fix_event_tags(scenario, bba_output, verbose)

    # Run oneSummary.py locally (only if writing to standard bba folder)
    if not output_dir:
        return run_summary(scenario, verbose)

    return True


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

    # Get convention cards from DLR properties
    cc1 = get_convention_card_ns(scenario)
    cc2 = get_convention_card_ew(scenario)

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

    # Fix Event tags with correct title from PBS
    fix_event_tags(scenario, bba_output, verbose)

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

    Dispatches based on BBA_MODE: "gui", "cli", or "mac".

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if BBA_MODE == "mac":
        return run_bba_mac(scenario, verbose)
    elif BBA_MODE == "cli":
        return run_bba_cli(scenario, verbose)
    else:
        return run_bba_gui(scenario, verbose)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run BBA analysis on a scenario")
    parser.add_argument("scenario", nargs="?", default="Smolen", help="Scenario name")
    parser.add_argument("--mac", action="store_true", help="Use bba-cli-mac (native Mac)")
    parser.add_argument("--cli", action="store_true", help="Use bba-cli.exe (Windows via SSH)")
    parser.add_argument("--compare", action="store_true",
                        help="Run Mac BBA and compare with existing Windows output")
    args = parser.parse_args()

    scenario = args.scenario

    if args.compare:
        # Run Mac BBA to a temp directory and compare with existing bba/ output
        compare_dir = os.path.join(PROJECT_ROOT, "bba-mac-test")
        print(f"Running bba-cli-mac on {scenario} (output to bba-mac-test/)...\n")
        success = run_bba_mac(scenario, verbose=True, output_dir=compare_dir)
        if success:
            mac_file = os.path.join(compare_dir, f"{scenario}.pbn")
            win_file = os.path.join(FOLDERS["bba"], f"{scenario}.pbn")
            if os.path.exists(win_file):
                print(f"\nComparing outputs...")
                print(f"  Windows: {win_file}")
                print(f"  Mac:     {mac_file}")
                # Use pbn-diff.py if available, otherwise basic diff
                pbn_diff = os.path.join(PROJECT_ROOT, "build-scripts-mac", "pbn-diff.py")
                if os.path.exists(pbn_diff):
                    result = subprocess.run(
                        [MAC_TOOLS["python"], pbn_diff, win_file, mac_file],
                        capture_output=True, text=True)
                    print(result.stdout)
                    if result.stderr:
                        print(result.stderr)
                else:
                    # Fallback: count boards and compare auction lines
                    for label, path in [("Windows", win_file), ("Mac", mac_file)]:
                        with open(path) as f:
                            content = f.read()
                        boards = content.count('[Board "')
                        auctions = content.count('[Auction "')
                        print(f"  {label}: {boards} boards, {auctions} auctions")
            else:
                print(f"\n  No existing Windows output at {win_file} to compare against.")
        print(f"\nResult: {'Success' if success else 'Failed'}")
    else:
        # Override mode if flags specified
        if args.mac:
            mode = "mac"
        elif args.cli:
            mode = "cli"
        else:
            mode = BBA_MODE

        mode_labels = {"gui": "GUI (BBA.exe watcher)", "cli": "CLI (bba-cli via SSH)", "mac": "Mac (bba-cli-mac native)"}
        print(f"Testing BBA operation with scenario: {scenario}\n")
        print(f"Mode: {mode_labels.get(mode, mode)}\n")

        # Temporarily override BBA_MODE for this run
        old_mode = BBA_MODE
        globals()['BBA_MODE'] = mode
        success = run_bba(scenario)
        globals()['BBA_MODE'] = old_mode
        print(f"\nResult: {'Success' if success else 'Failed'}")
