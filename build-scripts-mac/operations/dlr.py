"""
DLR operation: Extract dealer code from PBS files.
This is a Mac-native operation that wraps py/oneExtract.py.
"""
import os
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS


def run_dlr(scenario: str, verbose: bool = True) -> bool:
    """
    Extract dealer code from a PBS file to create a DLR file.

    PBS/{scenario} -> dlr/{scenario}.dlr

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- OneExtract.py: Creating dlr/{scenario}.dlr from PBS/{scenario}")

    # Check that PBS file exists
    pbs_path = os.path.join(FOLDERS["pbs"], scenario)
    if not os.path.exists(pbs_path):
        print(f"Error: PBS file not found: {pbs_path}")
        return False

    # Run oneExtract.py from the py directory
    py_dir = FOLDERS["py"]
    extract_script = os.path.join(py_dir, "oneExtract.py")

    if not os.path.exists(extract_script):
        print(f"Error: oneExtract.py not found: {extract_script}")
        return False

    try:
        result = subprocess.run(
            [MAC_TOOLS["python"], extract_script, "--scenario", scenario],
            cwd=py_dir,  # Run from py directory for relative paths
            capture_output=True,
            text=True,
            check=True,
        )

        if verbose and result.stdout:
            print(result.stdout)

        # Verify output was created
        dlr_path = os.path.join(FOLDERS["dlr"], f"{scenario}.dlr")
        if os.path.exists(dlr_path):
            return True
        else:
            print(f"Error: DLR file was not created: {dlr_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error running oneExtract.py: {e}")
        if e.stderr:
            print(e.stderr)
        return False


if __name__ == "__main__":
    # Test with a scenario
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        # Default test scenario
        scenario = "Smolen"

    print(f"Testing DLR operation with scenario: {scenario}\n")
    success = run_dlr(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
