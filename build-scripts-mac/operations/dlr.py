"""
DLR operation: Generate DLR file from BTN file.
Pipeline stage: BTN → DLR
  - Inlines #include directives
  - Adds # scenario-title metadata
  - Adds dealer statement from dealer-position metadata
"""
import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, PROJECT_ROOT


def generate_dlr(btn_path: str, scenario: str) -> str:
    """
    Generate DLR file content directly from a BTN file.

    The DLR is essentially the BTN with:
    - # scenario-title metadata added (from first line of chat)
    - dealer statement added below the chat block (from dealer-position metadata)
    - #include directives inlined
    - Existing 'dealer' statements in the code body skipped (we add it from metadata)
    """
    with open(btn_path, 'r', encoding='utf-8') as f:
        btn_lines = [line.rstrip('\n') for line in f.readlines()]

    # First pass: extract values we need
    dealer_position = 'S'
    chat_first_line = ''
    in_chat = False

    for line in btn_lines:
        stripped = line.strip()
        m = re.match(r'^#\s*dealer-position:\s*(.+)', stripped)
        if m:
            dealer_position = m.group(1).strip()
        if '/*@chat' in stripped:
            in_chat = True
            continue
        if '@chat*/' in stripped:
            in_chat = False
            continue
        if in_chat and stripped and not chat_first_line:
            chat_first_line = stripped

    dealer_map = {'S': 'south', 'N': 'north', 'E': 'east', 'W': 'west'}
    dealer_name = dealer_map.get(dealer_position.upper(), 'south')

    # Second pass: build DLR content
    output = []
    in_chat = False
    title_inserted = False

    for line in btn_lines:
        stripped = line.strip()

        # Insert # scenario-title after # button-text
        if not title_inserted and re.match(r'^#\s*button-text:', stripped):
            output.append(line)
            output.append(f"# scenario-title: {chat_first_line}")
            title_inserted = True
            continue

        # Keep the chat block as documentation
        if '/*@chat' in stripped:
            in_chat = True
            output.append(line)
            continue
        if '@chat*/' in stripped:
            in_chat = False
            output.append(line)
            # Add dealer statement after the chat block
            output.append(f"dealer {dealer_name}")
            continue
        if in_chat:
            output.append(line)
            continue

        # Skip existing 'dealer' statements in the code (we added it above)
        if re.match(r'^dealer\s+(south|north|east|west)', stripped):
            continue

        # Inline #include directives
        include_match = re.match(r'^#include\s+"([^"]+)"', stripped)
        if include_match:
            inc_path = include_match.group(1)
            full_path = os.path.join(PROJECT_ROOT, inc_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    output.append(f.read().rstrip())
            else:
                output.append(f"# ERROR: Could not find {inc_path}")
            continue

        # Copy everything else as-is
        output.append(line)

    # If no chat block was found, insert dealer after the metadata
    if not in_chat and f"dealer {dealer_name}" not in '\n'.join(output):
        # Find the first non-metadata, non-blank line and insert before it
        for i, line in enumerate(output):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped == '':
                output.insert(i, f"dealer {dealer_name}")
                break

    # Ensure scenario-title was inserted even without button-text
    if not title_inserted:
        output.insert(0, f"# scenario-title: {chat_first_line}")

    return '\n'.join(output) + '\n'


def run_dlr(scenario: str, verbose: bool = True) -> bool:
    """
    Generate DLR file from BTN file.

    btn/{scenario}.btn -> dlr/{scenario}.dlr

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Generating DLR from BTN for {scenario}")

    # Check that BTN file exists
    btn_path = os.path.join(FOLDERS["btn"], f"{scenario}.btn")
    if not os.path.exists(btn_path):
        print(f"Error: dlr: BTN file not found: {btn_path}")
        return False

    # Ensure output folder exists
    os.makedirs(FOLDERS["dlr"], exist_ok=True)

    try:
        if verbose:
            print(f"  Source: {btn_path}")

        dlr_content = generate_dlr(btn_path, scenario)

        dlr_path = os.path.join(FOLDERS["dlr"], f"{scenario}.dlr")
        with open(dlr_path, 'w', encoding='utf-8') as f:
            f.write(dlr_content)

        if verbose:
            print(f"  Created: {dlr_path}")

        return True

    except Exception as e:
        print(f"Error: dlr: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing DLR operation with scenario: {scenario}\n")
    success = run_dlr(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
