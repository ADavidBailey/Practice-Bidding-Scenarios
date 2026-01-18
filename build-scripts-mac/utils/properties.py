"""
Property fetching utilities for reading properties from .dlr files.
Replaces FetchProperty.cmd from Windows.
"""
import os
import re
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS


def fetch_property(scenario: str, property_name: str) -> Optional[str]:
    """
    Fetch a property value from a scenario's .dlr file.

    Properties are stored as comments in the format:
        # property-name: value

    Args:
        scenario: Scenario name (e.g., "Smolen")
        property_name: Property to fetch (e.g., "convention-card", "auction-filter")

    Returns:
        Property value if found, None otherwise
    """
    dlr_path = os.path.join(FOLDERS["dlr"], f"{scenario}.dlr")

    if not os.path.exists(dlr_path):
        print(f"Warning: DLR file not found: {dlr_path}")
        return None

    # Pattern to match property lines: # property-name: value
    # Also support lines without the # prefix
    pattern = re.compile(rf"^#?\s*{re.escape(property_name)}:\s*(.+)$", re.IGNORECASE)

    try:
        with open(dlr_path, "r") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    return match.group(1).strip()
    except Exception as e:
        print(f"Error reading {dlr_path}: {e}")

    return None


def get_convention_card(scenario: str) -> str:
    """
    Get the convention card for a scenario.

    Returns:
        Convention card name, or "21GF-DEFAULT" if not specified
    """
    from config import DEFAULT_CC1

    cc = fetch_property(scenario, "convention-card")
    return cc if cc else DEFAULT_CC1


def get_auction_filter(scenario: str) -> Optional[str]:
    """
    Get the auction filter expression for a scenario.

    Returns:
        Filter expression if found, None otherwise
    """
    return fetch_property(scenario, "auction-filter")


def get_button_text(scenario: str) -> Optional[str]:
    """
    Get the button text for a scenario.

    Returns:
        Button text if found, None otherwise
    """
    return fetch_property(scenario, "button-text")


def get_scenario_title(scenario: str) -> Optional[str]:
    """
    Get the scenario title.

    Returns:
        Scenario title if found, None otherwise
    """
    return fetch_property(scenario, "scenario-title")


if __name__ == "__main__":
    # Test with a sample scenario
    import glob

    # Find a scenario to test with
    dlr_files = glob.glob(os.path.join(FOLDERS["dlr"], "*.dlr"))
    if dlr_files:
        # Test with first scenario found
        test_scenario = os.path.splitext(os.path.basename(dlr_files[0]))[0]
        print(f"Testing with scenario: {test_scenario}\n")

        print(f"convention-card: {get_convention_card(test_scenario)}")
        print(f"auction-filter: {get_auction_filter(test_scenario)}")
        print(f"button-text: {get_button_text(test_scenario)}")
        print(f"scenario-title: {get_scenario_title(test_scenario)}")
    else:
        print("No .dlr files found to test with")
