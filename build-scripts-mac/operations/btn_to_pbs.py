"""
BTN to PBS operation: Generate PBS file from BTN file.
Transforms .btn format (with #include directives and metadata) into .pbs format.
"""
import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, PROJECT_ROOT

# Script directory for inlining includes
SCRIPT_DIR = os.path.join(PROJECT_ROOT, "script")


def parse_btn_file(btn_path: str) -> dict:
    """
    Parse a .btn file and extract metadata, chat content, and dealer code.

    Returns:
        dict with keys: alias, button_text, dealer_position, gib_works, bba_works,
                       auction_filter, chat, dealer_code
    """
    with open(btn_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'alias': None,
        'button_text': None,
        'dealer_position': 'S',  # default
        'gib_works': True,
        'bba_works': True,
        'auction_filter': None,
        'convention_card': None,
        'chat': None,
        'dealer_code': None,
    }

    # Parse single-line metadata: # key: value
    metadata_pattern = r'^#\s*(alias|button-text|dealer-position|gib-works|bba-works|auction-filter|convention-card):\s*(.*)$'
    for match in re.finditer(metadata_pattern, content, re.MULTILINE):
        key = match.group(1).lower().replace('-', '_')
        value = match.group(2).strip()

        if key in ('gib_works', 'bba_works'):
            result[key] = value.lower() == 'true'
        else:
            result[key] = value

    # Parse chat block: /*@chat ... @chat*/
    chat_match = re.search(r'/\*@chat\s*\n(.*?)@chat\*/', content, re.DOTALL)
    if chat_match:
        result['chat'] = chat_match.group(1).rstrip()

    # Extract dealer code (everything after the metadata/chat, excluding metadata comments)
    # Find where the actual dealer code starts (after metadata and chat block)
    lines = content.split('\n')
    dealer_lines = []
    in_chat_block = False
    past_metadata = False

    for line in lines:
        # Track chat block
        if '/*@chat' in line:
            in_chat_block = True
            continue
        if '@chat*/' in line:
            in_chat_block = False
            continue
        if in_chat_block:
            continue

        # Skip metadata lines at the top
        if not past_metadata:
            if re.match(r'^#\s*(alias|button-text|dealer-position|gib-works|bba-works|auction-filter):', line):
                continue
            if line.strip() == '':
                continue
            past_metadata = True

        dealer_lines.append(line)

    result['dealer_code'] = '\n'.join(dealer_lines)

    return result


def inline_includes(dealer_code: str) -> str:
    """
    Inline #include "script/..." directives by reading the referenced files.
    """
    def replace_include(match):
        path = match.group(1)
        # Resolve the path relative to project root
        full_path = os.path.join(PROJECT_ROOT, path)

        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().rstrip()
            return content
        else:
            # If file not found, leave a comment
            return f"# ERROR: Could not find {path}"

    # Match #include "path"
    pattern = r'#include\s+"([^"]+)"'
    return re.sub(pattern, replace_include, dealer_code)


def generate_logging_code(alias: str, scenario_filename: str) -> str:
    """
    Generate the scenario logging JavaScript code.
    """
    return f"""window.currentPBSScenario = '{alias}';
window.currentPBSScenarioFilename = '{scenario_filename}';
console.log('PBS: Logging scenario selection for {alias}');
fetch('https://bba.harmonicsystems.com/api/scenario/select', {{
    method: 'POST',
    headers: {{
        'Content-Type': 'application/json',
        'X-Client-Version': '1.0.0'
    }},
    body: JSON.stringify({{
        scenario: '{alias}',
        user: whoAmI() || 'anonymous'
    }})
}}).then(function(r){{ console.log('PBS: Server response', r.status); }}).catch(function(e){{ console.log('PBS: Fetch error', e); }});"""


def generate_pbs(parsed: dict, scenario_filename: str) -> str:
    """
    Generate PBS file content from parsed BTN data.
    """
    alias = parsed['alias'] or 'Unknown'
    button_text = parsed['button_text'] or alias
    dealer_position = parsed['dealer_position'] or 'S'

    # Inline includes in dealer code
    dealer_code = inline_includes(parsed['dealer_code'])

    # Remove "action printpbn" line - not needed in PBS
    dealer_code = re.sub(r'\n*action\s+printpbn\s*\n*', '\n', dealer_code)

    # Build the PBS content
    lines = []

    # Script block with logging code
    lines.append(f"Script,{alias}")
    lines.append(generate_logging_code(alias, scenario_filename))
    lines.append("setDealerCode(`")

    # Add auction filter and convention card if present (as block comment)
    if parsed['auction_filter'] or parsed['convention_card']:
        lines.append("")
        lines.append("/*")
        if parsed['convention_card']:
            lines.append(f"convention-card: {parsed['convention_card']}")
        if parsed['auction_filter']:
            lines.append(f"auction-filter: {parsed['auction_filter']}")
        lines.append("*/")

    # Add dealer code
    lines.append(dealer_code.rstrip())

    # Close setDealerCode
    lines.append(f"`, \"{dealer_position}\", true)")
    lines.append("Script")

    # Button definition
    if parsed['chat']:
        # Convert regular commas to wide commas in chat content
        # Replace ", " with "，" (wide comma absorbs the trailing space)
        chat_content = parsed['chat'].replace(', ', '，')
        # Format chat with line continuations
        chat_lines = chat_content.split('\n')
        chat_formatted = '\\n\\\n'.join(chat_lines)
        lines.append(f"Button,{button_text},\\n\\")
        lines.append(f"{chat_formatted}\\n\\")
        lines.append(f"%{alias}%")
    else:
        lines.append(f"Button,{button_text},%{alias}%")

    lines.append("")  # trailing newline

    return '\n'.join(lines)


def run_btn_to_pbs(scenario: str, verbose: bool = True) -> bool:
    """
    Generate PBS file from BTN file.

    btn/{scenario}.btn -> pbs-test/{scenario}.pbs

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Generating PBS from BTN for {scenario}")

    # Check that BTN file exists
    btn_path = os.path.join(FOLDERS["btn"], f"{scenario}.btn")
    if not os.path.exists(btn_path):
        print(f"Error: btnToPbs: BTN file not found: {btn_path}")
        return False

    # Ensure output folder exists
    os.makedirs(FOLDERS["pbs_test"], exist_ok=True)

    try:
        # Parse BTN file
        if verbose:
            print(f"  Parsing: {btn_path}")
        parsed = parse_btn_file(btn_path)

        # Generate PBS content
        pbs_content = generate_pbs(parsed, scenario)

        # Write PBS file with .pbs extension
        pbs_path = os.path.join(FOLDERS["pbs_test"], f"{scenario}.pbs")
        with open(pbs_path, 'w', encoding='utf-8') as f:
            f.write(pbs_content)

        if verbose:
            print(f"  Created: {pbs_path}")

        return True

    except Exception as e:
        print(f"Error: btnToPbs: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing btnToPbs operation with scenario: {scenario}\n")
    success = run_btn_to_pbs(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
