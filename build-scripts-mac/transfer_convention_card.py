#!/usr/bin/env python3
"""
Transfer convention-card metadata from PBS files to BTN files.
Only transfers non-empty values.
"""
import os
import re
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FOLDERS

def get_convention_card_from_pbs(pbs_path: str):
    """Extract convention-card value from PBS file."""
    with open(pbs_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match convention-card with value on the SAME LINE (not grabbing the next line)
    # Formats: "# convention-card: value" or "convention-card: value"
    # Value must be non-empty and not contain "auction-filter" (which would be the next line)
    match = re.search(r'^#?\s*convention-card:\s*(\S[^\n]*?)$', content, re.MULTILINE)
    if match:
        value = match.group(1).strip()
        # Exclude if it looks like an auction-filter was incorrectly captured
        if value and not value.startswith('auction-filter') and not value.startswith('#'):
            return value
    return None

def add_convention_card_to_btn(btn_path: str, convention_card: str) -> bool:
    """Add convention-card metadata to BTN file if not already present."""
    with open(btn_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already has convention-card
    if re.search(r'^#\s*convention-card:', content, re.MULTILINE):
        return False  # Already has it

    # Find where to insert (after auction-filter if present, else after bba-works)
    lines = content.split('\n')
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Insert after auction-filter line
        if not inserted and line.startswith('# auction-filter:'):
            new_lines.append(f"# convention-card: {convention_card}")
            inserted = True
        # Or insert after bba-works line (if no auction-filter)
        elif not inserted and line.startswith('# bba-works:'):
            # Check if next line is auction-filter
            if i + 1 < len(lines) and lines[i + 1].startswith('# auction-filter:'):
                continue  # Will insert after auction-filter instead
            new_lines.append(f"# convention-card: {convention_card}")
            inserted = True

    if inserted:
        with open(btn_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

def main():
    pbs_dir = FOLDERS["pbs"]
    btn_dir = FOLDERS["btn"]

    transferred = 0
    skipped = 0
    not_found = 0

    # Get all PBS files
    for filename in sorted(os.listdir(pbs_dir)):
        if filename.startswith('.'):
            continue

        pbs_path = os.path.join(pbs_dir, filename)
        if not os.path.isfile(pbs_path):
            continue

        # Get convention-card from PBS
        convention_card = get_convention_card_from_pbs(pbs_path)
        if not convention_card:
            continue

        # Find corresponding BTN file
        btn_path = os.path.join(btn_dir, f"{filename}.btn")
        if not os.path.exists(btn_path):
            print(f"BTN not found: {filename}")
            not_found += 1
            continue

        # Add to BTN file
        if add_convention_card_to_btn(btn_path, convention_card):
            print(f"Added to {filename}.btn: {convention_card}")
            transferred += 1
        else:
            skipped += 1

    print(f"\nDone: {transferred} transferred, {skipped} skipped (already present), {not_found} not found")

if __name__ == "__main__":
    main()
