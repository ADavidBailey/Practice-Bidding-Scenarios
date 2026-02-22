"""
Property fetching utilities for reading properties from .dlr files.
Replaces FetchProperty.cmd from Windows.
"""
import os
import re
import sys
from typing import Dict, Optional

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


def get_convention_card_ns(scenario: str) -> str:
    """
    Get the NS convention card for a scenario.

    Returns:
        Convention card name, or DEFAULT_CC1 if not specified
    """
    from config import DEFAULT_CC1

    cc = fetch_property(scenario, "convention-card-ns")
    return cc if cc else DEFAULT_CC1


def get_convention_card_ew(scenario: str) -> str:
    """
    Get the EW convention card for a scenario.

    Returns:
        Convention card name, or DEFAULT_CC2 if not specified
    """
    from config import DEFAULT_CC2

    cc = fetch_property(scenario, "convention-card-ew")
    return cc if cc else DEFAULT_CC2


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


def get_quiz_control(scenario: str) -> Dict[str, object]:
    """
    Get the quiz-control settings for a scenario.

    Parses "rounds=3,level=game" format from the quiz-control property.

    Returns:
        Dict with 'rounds' (int) and 'level' (str) keys.
        Defaults to {'rounds': 3, 'level': 'game'} if not specified.
    """
    defaults = {'rounds': 3, 'level': 'game'}
    raw = fetch_property(scenario, "quiz-control")
    if not raw:
        return defaults

    for part in raw.split(','):
        key, _, value = part.strip().partition('=')
        key = key.strip()
        value = value.strip()
        if key == 'rounds':
            try:
                defaults['rounds'] = int(value)
            except ValueError:
                pass
        elif key == 'level':
            defaults['level'] = value

    return defaults


def get_btn_property(scenario: str, property_name: str) -> Optional[str]:
    """
    Fetch a property value directly from a scenario's .btn file.

    Args:
        scenario: Scenario name (e.g., "Smolen")
        property_name: Property to fetch (e.g., "button-text")

    Returns:
        Property value if found, None otherwise
    """
    btn_path = os.path.join(FOLDERS["btn"], f"{scenario}.btn")

    if not os.path.exists(btn_path):
        return None

    pattern = re.compile(rf'^#\s*{re.escape(property_name)}:\s*(.+)$', re.IGNORECASE)

    try:
        with open(btn_path, "r") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    return match.group(1).strip()
    except Exception:
        pass

    return None


def get_chat_text(scenario: str) -> str:
    """
    Get the chat text from a scenario's .btn file.

    Reads content between /*@chat and @chat*/ markers,
    stripping leading '---' lines.

    Returns:
        Chat text as a single string, or empty string if not found.
    """
    btn_path = os.path.join(FOLDERS["btn"], f"{scenario}.btn")

    if not os.path.exists(btn_path):
        return ""

    try:
        with open(btn_path, "r") as f:
            content = f.read()
    except Exception:
        return ""

    match = re.search(r'/\*@chat\s*\n(.*?)@chat\*/', content, re.DOTALL)
    if not match:
        return ""

    lines = []
    for line in match.group(1).strip().splitlines():
        line = line.strip()
        if line.startswith("---"):
            line = line.lstrip("-").strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def get_bba_works(scenario: str) -> bool:
    """
    Check if BBA analysis works for a scenario.
    Reads directly from BTN file (source of truth).

    Args:
        scenario: Scenario name (e.g., "Smolen")

    Returns:
        True only if bba-works is explicitly set to true.
        False if BTN file doesn't exist, bba-works line is missing, or bba-works is false.
    """
    btn_path = os.path.join(FOLDERS["btn"], f"{scenario}.btn")

    if not os.path.exists(btn_path):
        return False  # Default to false if BTN not found

    pattern = re.compile(r'^#\s*bba-works:\s*(.+)$', re.IGNORECASE)

    try:
        with open(btn_path, "r") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    return match.group(1).strip().lower() == 'true'
    except Exception:
        pass

    return False  # Default to false if bba-works line not found


if __name__ == "__main__":
    # Test with a sample scenario
    import glob

    # Find a scenario to test with
    dlr_files = glob.glob(os.path.join(FOLDERS["dlr"], "*.dlr"))
    if dlr_files:
        # Test with first scenario found
        test_scenario = os.path.splitext(os.path.basename(dlr_files[0]))[0]
        print(f"Testing with scenario: {test_scenario}\n")

        print(f"convention-card-ns: {get_convention_card_ns(test_scenario)}")
        print(f"convention-card-ew: {get_convention_card_ew(test_scenario)}")
        print(f"auction-filter: {get_auction_filter(test_scenario)}")
        print(f"button-text: {get_button_text(test_scenario)}")
        print(f"scenario-title: {get_scenario_title(test_scenario)}")
    else:
        print("No .dlr files found to test with")
