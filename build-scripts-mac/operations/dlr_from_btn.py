"""
DLR operation: Generate DLR file from BTN file.
Pipeline stage: BTN → DLR
  - Inlines #include directives
  - Adds # scenario-title metadata (from first line of chat)
  - Dealer statement is preserved from the BTN file as-is
  - Ensures 'action printoneline,' is present before any average/frequency
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
    - #include directives inlined
    - dealer statement preserved from BTN as-is
    - 'action printoneline,' ensured before any average/frequency statements
    """
    with open(btn_path, 'r', encoding='utf-8') as f:
        btn_lines = [line.rstrip('\n') for line in f.readlines()]

    # First pass: extract chat first line for scenario-title
    chat_first_line = ''
    in_chat = False

    for line in btn_lines:
        stripped = line.strip()
        if '/*@chat' in stripped:
            in_chat = True
            continue
        if '@chat*/' in stripped:
            in_chat = False
            continue
        if in_chat and stripped and not chat_first_line:
            chat_first_line = stripped

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
            continue
        if in_chat:
            output.append(line)
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

        # Copy everything else as-is (including dealer statement)
        output.append(line)

    # Ensure scenario-title was inserted even without button-text
    if not title_inserted:
        output.insert(0, f"# scenario-title: {chat_first_line}")

    # Post-process: ensure 'action printoneline,' is present
    output = _ensure_action_printoneline(output)

    return '\n'.join(output) + '\n'


def _ensure_action_printoneline(lines: list) -> list:
    """
    Ensure 'action printoneline,' appears in the output.
    - Replace any existing 'action' line with 'action printoneline,'
    - Remove any standalone printoneline/# printoneline lines that follow
    - If no action line exists, insert before first average/frequency
    - If no average/frequency either, append at the end
    """
    result = []
    action_found = False
    just_inserted_action = False

    for line in lines:
        stripped = line.strip()

        # Replace existing bare 'action' with 'action printoneline,'
        if stripped == 'action':
            result.append('action printoneline,')
            action_found = True
            just_inserted_action = True
            continue

        # Skip standalone printoneline lines right after action
        if just_inserted_action and re.match(r'^#?\s*printoneline\s*,?\s*$', stripped):
            continue

        # Any other non-blank line clears the just-inserted flag
        if stripped:
            just_inserted_action = False

        # If no action yet and we hit the first average/frequency, insert before it
        if not action_found and re.match(r'^(average|frequency)\b', stripped):
            result.append('action printoneline,')
            action_found = True

        result.append(line)

    # If still no action, append at the end
    if not action_found:
        # Remove trailing blank lines, add action, then restore one blank line
        while result and result[-1].strip() == '':
            result.pop()
        result.append('action printoneline,')

    return result


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
