"""
Path utilities for translating between Mac and Windows paths.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PROJECT_ROOT, FOLDERS, DRIVE_MAPPINGS


def mac_to_windows(mac_path: str) -> str:
    """
    Convert a Mac path to a Windows path using drive mappings.

    Example:
        /Users/rick/Developer/GitHub/Practice-Bidding-Scenarios/pbn/Smolen.pbn
        -> P:\\pbn\\Smolen.pbn
    """
    # Normalize the path
    mac_path = os.path.abspath(mac_path)

    # Find the matching drive mapping
    for mac_base, windows_drive in DRIVE_MAPPINGS.items():
        if mac_path.startswith(mac_base):
            # Replace Mac base with Windows drive and convert slashes
            relative_path = mac_path[len(mac_base):]
            windows_path = windows_drive + relative_path.replace("/", "\\")
            return windows_path

    # No mapping found
    raise ValueError(f"No drive mapping found for: {mac_path}")


def windows_to_mac(windows_path: str) -> str:
    """
    Convert a Windows path to a Mac path using drive mappings.

    Example:
        P:\\pbn\\Smolen.pbn
        -> /Users/rick/Developer/GitHub/Practice-Bidding-Scenarios/pbn/Smolen.pbn
    """
    # Normalize the path
    windows_path = windows_path.replace("/", "\\")

    # Find the matching drive mapping
    for mac_base, windows_drive in DRIVE_MAPPINGS.items():
        if windows_path.upper().startswith(windows_drive.upper()):
            # Replace Windows drive with Mac base and convert slashes
            relative_path = windows_path[len(windows_drive):]
            mac_path = mac_base + relative_path.replace("\\", "/")
            return mac_path

    # No mapping found
    raise ValueError(f"No drive mapping found for: {windows_path}")


def get_scenario_path(scenario: str, folder_key: str, extension: str = "") -> str:
    """
    Get the full Mac path for a scenario file.

    Args:
        scenario: Scenario name (e.g., "Smolen")
        folder_key: Key from FOLDERS config (e.g., "pbn", "dlr", "bba")
        extension: File extension including dot (e.g., ".pbn", ".dlr")

    Returns:
        Full Mac path to the file
    """
    folder = FOLDERS.get(folder_key)
    if not folder:
        raise ValueError(f"Unknown folder key: {folder_key}")

    filename = f"{scenario}{extension}"
    return os.path.join(folder, filename)


def get_windows_scenario_path(scenario: str, folder_key: str, extension: str = "") -> str:
    """
    Get the Windows path for a scenario file.

    Args:
        scenario: Scenario name (e.g., "Smolen")
        folder_key: Key from FOLDERS config (e.g., "pbn", "dlr", "bba")
        extension: File extension including dot (e.g., ".pbn", ".dlr")

    Returns:
        Windows path to the file (e.g., P:\\pbn\\Smolen.pbn)
    """
    mac_path = get_scenario_path(scenario, folder_key, extension)
    return mac_to_windows(mac_path)


if __name__ == "__main__":
    # Test path conversions
    print("Path conversion tests:\n")

    # Test scenario paths
    for folder in ["dlr", "pbn", "bba", "bba_filtered"]:
        mac_path = get_scenario_path("Smolen", folder, ".pbn" if folder != "dlr" else ".dlr")
        win_path = mac_to_windows(mac_path)
        print(f"{folder}:")
        print(f"  Mac: {mac_path}")
        print(f"  Win: {win_path}")
        print()
