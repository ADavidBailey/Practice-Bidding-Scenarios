#!/usr/bin/env python3
"""
Extract button width and color from original PBS files and add to BTN metadata.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROJECT_ROOT

def extract_button_style(pbs_path):
    """Extract width and color from PBS file's Button line."""
    with open(pbs_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the Button line with style info
    # Pattern: %alias%,width=XX% [color=YYY] [backgroundColor=ZZZ]
    # or just: %alias%

    width = None
    color = None

    # Look for width=XX%
    width_match = re.search(r'width=(\d+(?:\.\d+)?%)', content)
    if width_match:
        width = width_match.group(1)
        # Skip 100% widths (those are full-width non-GIB scenarios)
        if width == '100%':
            width = None

    # Look for color=XXX (not backgroundColor)
    color_match = re.search(r'(?<!background)[cC]olor=(\w+)', content)
    if color_match:
        color = color_match.group(1)

    return width, color


def update_btn_metadata(btn_path, width, color):
    """Add or update button-width and button-color in BTN file metadata header."""
    with open(btn_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')

    # First, remove any existing button-width/button-color lines from anywhere
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# button-width:') or stripped.startswith('# button-color:'):
            continue
        filtered_lines.append(line)

    # Find the last metadata line (# comment at top of file)
    # Metadata ends when we hit an empty line or non-# line
    last_metadata_idx = -1
    for i, line in enumerate(filtered_lines):
        stripped = line.strip()
        if stripped.startswith('#') and not stripped.startswith('#include'):
            last_metadata_idx = i
        elif stripped == '':
            # Empty line - check if next non-empty line is still metadata
            continue
        else:
            # Non-metadata line found
            break

    # Insert new metadata after the last metadata line
    result_lines = []
    for i, line in enumerate(filtered_lines):
        result_lines.append(line)
        if i == last_metadata_idx:
            if width:
                result_lines.append(f'# button-width: {width}')
            if color:
                result_lines.append(f'# button-color: {color}')

    new_content = '\n'.join(result_lines)

    if new_content != content:
        with open(btn_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    pbs_archive = os.path.join(PROJECT_ROOT, "pbs-archive")
    btn_dir = os.path.join(PROJECT_ROOT, "btn")

    updated = 0
    skipped = 0

    for filename in sorted(os.listdir(pbs_archive)):
        if filename.startswith('.'):
            continue

        pbs_path = os.path.join(pbs_archive, filename)
        if not os.path.isfile(pbs_path):
            continue

        # Extract style info
        width, color = extract_button_style(pbs_path)

        if not width and not color:
            continue

        # Find corresponding BTN file
        btn_path = os.path.join(btn_dir, f"{filename}.btn")
        if not os.path.exists(btn_path):
            print(f"BTN not found: {filename}")
            skipped += 1
            continue

        # Update BTN file
        if update_btn_metadata(btn_path, width, color):
            style_info = []
            if width:
                style_info.append(f"width={width}")
            if color:
                style_info.append(f"color={color}")
            print(f"Updated: {filename}.btn -> {', '.join(style_info)}")
            updated += 1

    print(f"\nDone: {updated} updated, {skipped} BTN not found")


if __name__ == "__main__":
    main()
