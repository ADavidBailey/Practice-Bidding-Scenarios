"""
BTN to PBS operation: Generate PBS and DLR files from BTN file.
Transforms .btn format (with #include directives and metadata) into:
  - .pbs format (for BBOalert button definitions)
  - .dlr format (for dealer hand generation)
Button width and color are derived from the layout file, not the BTN file.
"""
import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, PROJECT_ROOT

# Script directory for inlining includes
SCRIPT_DIR = os.path.join(PROJECT_ROOT, "script")

# Cache for layout styles (loaded once)
_layout_styles = None


def load_layout_styles():
    """
    Parse the layout file and extract button width/color for each scenario.
    Returns dict mapping scenario name -> {'width': '12%', 'color': 'blue'}
    """
    global _layout_styles
    if _layout_styles is not None:
        return _layout_styles

    _layout_styles = {}
    layout_path = os.path.join(FOLDERS["btn"], "-layout.txt")

    if not os.path.exists(layout_path):
        return _layout_styles

    with open(layout_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('[') or stripped == '---':
                continue

            # Parse button row, handling groups
            buttons = parse_layout_buttons(stripped)
            for btn in buttons:
                name = btn['name']
                if btn.get('width') or btn.get('color'):
                    _layout_styles[name] = {
                        'width': btn.get('width'),
                        'color': btn.get('color'),
                    }

    return _layout_styles


def parse_layout_buttons(line):
    """Parse a button row line from layout file, handling groups."""
    buttons = []

    # Split by comma but respect parentheses
    parts = []
    current = ""
    paren_depth = 0

    for char in line:
        if char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif char == ',' and paren_depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())

    for part in parts:
        part = part.strip()
        if part.startswith('(') and part.endswith(')'):
            # Grouped buttons - they share 50% width
            group_content = part[1:-1]
            group_items = [s.strip() for s in group_content.split(',')]

            # Calculate width for each button in group
            total_width = 50
            n = len(group_items)
            base_width = total_width // n
            remainder = total_width % n

            for i, item in enumerate(group_items):
                item_parts = item.split(':')
                name = item_parts[0]
                color = None
                item_width = None
                for p in item_parts[1:]:
                    if p.endswith('%'):
                        item_width = p
                    else:
                        color = p
                # Use explicit width if provided, otherwise calculate
                if item_width is None:
                    item_width = f"{base_width + (1 if i >= n - remainder else 0)}%"
                buttons.append({'name': name, 'width': item_width, 'color': color, 'grouped': True})
        else:
            # Regular button - may have explicit width like file:blue:38%
            item_parts = part.split(':')
            name = item_parts[0]
            color = None
            width = None
            for p in item_parts[1:]:
                if p.endswith('%'):
                    width = p
                else:
                    color = p
            buttons.append({'name': name, 'width': width, 'color': color, 'grouped': False})

    # Calculate widths for non-grouped buttons
    non_grouped = [b for b in buttons if not b.get('grouped')]
    grouped = [b for b in buttons if b.get('grouped')]

    if len(non_grouped) == 1 and len(grouped) == 0:
        non_grouped[0]['width'] = '100%'
    elif len(non_grouped) == 2 and len(grouped) == 0:
        for b in non_grouped:
            b['width'] = '50%'
    elif len(non_grouped) == 1 and len(grouped) > 0:
        non_grouped[0]['width'] = '50%'
    elif len(non_grouped) == 2:
        for b in non_grouped:
            b['width'] = '50%'

    return buttons


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
    Button width and color are derived from the layout file, not the BTN file.
    """
    alias = parsed['alias'] or 'Unknown'
    button_text = parsed['button_text'] or alias
    dealer_position = parsed['dealer_position'] or 'S'

    # Get layout styles for this scenario
    layout_styles = load_layout_styles()
    scenario_style = layout_styles.get(scenario_filename, {})

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
    # Build style string from layout file (width and color)
    style_parts = []

    # Width from layout file
    if scenario_style.get('width'):
        style_parts.append(f"width={scenario_style['width']}")

    # Color: lightpink background if GIB doesn't work, else text color from layout
    if not parsed['gib_works']:
        style_parts.append("backgroundColor=lightpink")
    elif scenario_style.get('color'):
        style_parts.append(f"color={scenario_style['color']}")

    style_str = " ".join(style_parts)
    if style_str:
        style_str = "," + style_str

    if parsed['chat']:
        # Convert regular commas to wide commas in chat content
        # Replace ", " with "，" (wide comma absorbs the trailing space)
        chat_content = parsed['chat'].replace(', ', '，')
        # Format chat with line continuations
        chat_lines = chat_content.split('\n')
        chat_formatted = '\\n\\\n'.join(chat_lines)
        lines.append(f"Button,{button_text},\\n\\")
        lines.append(f"{chat_formatted}\\n\\")
        lines.append(f"%{alias}%{style_str}")
    else:
        lines.append(f"Button,{button_text},%{alias}%{style_str}")

    lines.append("")  # trailing newline

    return '\n'.join(lines)


def generate_dlr(parsed: dict, scenario: str) -> str:
    """
    Generate DLR file content from parsed BTN data.
    """
    dealer_position = parsed['dealer_position'] or 'S'
    button_text = parsed['button_text'] or scenario

    # Map dealer position to full name
    dealer_map = {'S': 'south', 'N': 'north', 'E': 'east', 'W': 'west'}
    dealer_name = dealer_map.get(dealer_position.upper(), 'south')

    # Inline includes in dealer code
    dealer_code = inline_includes(parsed['dealer_code'])

    lines = []

    # Header comments
    lines.append(f"# button-text: {button_text}")
    # Replace ", " with wide comma in scenario-title (same as PBS chat content)
    scenario_title = parsed.get('chat', '').split(chr(10))[0] if parsed.get('chat') else ''
    scenario_title = scenario_title.replace(', ', '，')
    lines.append(f"# scenario-title: {scenario_title}")
    if parsed.get('auction_filter'):
        lines.append(f"# auction-filter: {parsed['auction_filter']}")
    if parsed.get('convention_card'):
        lines.append(f"# convention-card: {parsed['convention_card']}")
    lines.append(f"# {scenario}")
    lines.append(f"dealer {dealer_name}")

    # Process dealer code - remove dealer/generate/produce/printoneline statements
    has_action = False
    for line in dealer_code.split('\n'):
        stripped = line.strip()
        # Skip these lines - they'll be added by the pipeline
        if stripped.startswith('dealer '):
            continue
        if stripped.startswith('generate '):
            continue
        if stripped.startswith('produce '):
            continue
        if stripped.startswith('printoneline'):
            continue
        if stripped.startswith('action'):
            has_action = True
        lines.append(line)

    # Add action if not present
    if not has_action:
        lines.append("action printpbn")
    else:
        lines.append("printpbn")

    lines.append("")  # trailing newline

    return '\n'.join(lines)


def run_btn_to_pbs(scenario: str, verbose: bool = True) -> bool:
    """
    Generate PBS and DLR files from BTN file.

    btn/{scenario}.btn -> pbs-test/{scenario}.pbs
    btn/{scenario}.btn -> dlr/{scenario}.dlr

    Args:
        scenario: Scenario name (e.g., "Smolen")
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Generating PBS and DLR from BTN for {scenario}")

    # Check that BTN file exists
    btn_path = os.path.join(FOLDERS["btn"], f"{scenario}.btn")
    if not os.path.exists(btn_path):
        print(f"Error: btnToPbs: BTN file not found: {btn_path}")
        return False

    # Ensure output folders exist
    os.makedirs(FOLDERS["pbs_test"], exist_ok=True)
    os.makedirs(FOLDERS["dlr"], exist_ok=True)

    try:
        # Parse BTN file
        if verbose:
            print(f"  Parsing: {btn_path}")
        parsed = parse_btn_file(btn_path)

        # Generate PBS content
        pbs_content = generate_pbs(parsed, scenario)

        # Determine whether to write to pbs-test
        pbs_test_path = os.path.join(FOLDERS["pbs_test"], f"{scenario}.pbs")
        pbs_release_path = os.path.join(FOLDERS["pbs_release"], f"{scenario}.pbs")

        # Check if pbs-test file already exists (scenario was already modified)
        pbs_test_exists = os.path.exists(pbs_test_path)

        # Check if content differs from pbs-release
        content_differs = True  # Default to True if no release file exists
        if os.path.exists(pbs_release_path):
            with open(pbs_release_path, 'r', encoding='utf-8') as f:
                release_content = f.read()
            content_differs = (pbs_content != release_content)

        # Only write to pbs-test if:
        # - pbs-test file already exists (was already modified), OR
        # - Content differs from pbs-release
        if pbs_test_exists or content_differs:
            with open(pbs_test_path, 'w', encoding='utf-8') as f:
                f.write(pbs_content)
            if verbose:
                if not content_differs:
                    print(f"  Updated: {pbs_test_path} (unchanged from release)")
                else:
                    print(f"  Created: {pbs_test_path}")
        else:
            if verbose:
                print(f"  Skipped: {pbs_test_path} (matches release)")

        # Generate DLR content
        dlr_content = generate_dlr(parsed, scenario)

        # Write DLR file
        dlr_path = os.path.join(FOLDERS["dlr"], f"{scenario}.dlr")
        with open(dlr_path, 'w', encoding='utf-8') as f:
            f.write(dlr_content)

        if verbose:
            print(f"  Created: {dlr_path}")

        return True

    except Exception as e:
        print(f"Error: btnToPbs: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Smolen"

    print(f"Testing btnToPbs operation with scenario: {scenario}\n")
    success = run_btn_to_pbs(scenario)
    print(f"\nResult: {'Success' if success else 'Failed'}")
