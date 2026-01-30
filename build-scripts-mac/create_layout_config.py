#!/usr/bin/env python3
"""
Create button layout config from existing -PBS-logging.txt
"""
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROJECT_ROOT

def main():
    # Read the alias mapping from Import declarations
    pbs_logging = os.path.join(PROJECT_ROOT, "-PBS-logging.txt")
    with open(pbs_logging, 'r', encoding='utf-8') as f:
        content = f.read()

    # Build alias -> filename mapping
    alias_map = {}
    for match in re.finditer(r'^Import,([^,]+),.*pbs-test/([^.]+)\.pbs', content, re.MULTILINE):
        alias = match.group(1)
        filename = match.group(2)
        alias_map[alias] = filename

    # Process button layout section (starts after imports, around line 560)
    lines = content.split('\n')
    output = []
    output.append("# Button Layout Configuration")
    output.append("# Generated from -PBS-logging.txt")
    output.append("#")
    output.append("# Format:")
    output.append("#   [Major] Title           - Major header (LemonChiffon)")
    output.append("#   [Section] Title         - Section header (lightblue, collapsible)")
    output.append("#   [Action] Text|script|width - Action button (lightgreen)")
    output.append("#   ---                     - Separator row")
    output.append("#   file1, file2, ...       - Button row (BTN filenames without .btn)")
    output.append("#   # comment               - Comment line")
    output.append("")

    in_layout = False
    current_row = []

    for line in lines:
        line = line.strip()

        # Start of layout section
        if 'Option,Practice Table' in line:
            in_layout = True
            continue

        # End of layout
        if line == 'Option':
            break

        if not in_layout:
            continue

        # Skip empty lines
        if not line:
            if current_row:
                output.append(', '.join(current_row))
                current_row = []
            continue

        # Major header (LemonChiffon)
        if 'backgroundColor=LemonChiffon' in line:
            if current_row:
                output.append(', '.join(current_row))
                current_row = []
            match = re.match(r'Button,([^,]+)', line)
            if match:
                title = match.group(1)
                output.append("")
                output.append(f"[Major] {title}")
            continue

        # Section header (lightblue)
        if 'backgroundColor=lightblue' in line:
            if current_row:
                output.append(', '.join(current_row))
                current_row = []
            match = re.match(r'Button,([^,]+)', line)
            if match:
                title = match.group(1)
                output.append("")
                output.append(f"[Section] {title}")
            continue

        # Action button (lightgreen)
        if 'backgroundColor=lightgreen' in line:
            if current_row:
                output.append(', '.join(current_row))
                current_row = []
            match = re.match(r'Button,([^,]+),(%[^%]+%),width=(\d+)%', line)
            if match:
                text = match.group(1)
                script = match.group(2)
                width = match.group(3)
                output.append(f"[Action] {text}|{script}|{width}")
            continue

        # Separator
        if line == 'Button,---':
            if current_row:
                output.append(', '.join(current_row))
                current_row = []
            output.append("---")
            continue

        # Import statement (scenario button)
        if line.startswith('Import,'):
            alias = line.split(',')[1]
            if alias in alias_map:
                current_row.append(alias_map[alias])
            else:
                # Alias not found, use as-is (might be missing)
                output.append(f"# MISSING: {alias}")
            continue

        # Commented import
        if line.startswith('#Import,'):
            alias = line.split(',')[1]
            if alias in alias_map:
                output.append(f"# {alias_map[alias]}")
            continue

        # Script definitions - skip
        if line.startswith('Script,'):
            continue

        # Commented lines
        if line.startswith('#'):
            continue

    # Flush remaining
    if current_row:
        output.append(', '.join(current_row))

    # Write output
    output_path = os.path.join(PROJECT_ROOT, "btn", "-layout.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f"Created: {output_path}")
    print(f"Alias mappings: {len(alias_map)}")

if __name__ == "__main__":
    main()
