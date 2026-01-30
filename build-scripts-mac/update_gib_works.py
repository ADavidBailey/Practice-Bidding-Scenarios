#!/usr/bin/env python3
"""
Update gib-works metadata in BTN files based on lightpink usage in original PBS files.
Files with lightpink in PBS indicate scenarios not supported by GIB bots.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import FOLDERS

def has_lightpink(pbs_path: str) -> bool:
    """Check if PBS file uses lightpink background."""
    with open(pbs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return 'lightpink' in content.lower()

def update_gib_works(btn_path: str, gib_works: bool) -> bool:
    """Update gib-works value in BTN file."""
    with open(btn_path, 'r', encoding='utf-8') as f:
        content = f.read()

    value = 'true' if gib_works else 'false'
    new_content = re.sub(
        r'^(#\s*gib-works:\s*).*$',
        f'\\g<1>{value}',
        content,
        flags=re.MULTILINE
    )

    if new_content != content:
        with open(btn_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    pbs_dir = FOLDERS["pbs"]
    btn_dir = FOLDERS["btn"]

    updated = 0
    skipped = 0
    not_found = 0

    for filename in sorted(os.listdir(pbs_dir)):
        if filename.startswith('.'):
            continue

        pbs_path = os.path.join(pbs_dir, filename)
        if not os.path.isfile(pbs_path):
            continue

        # Check if PBS has lightpink
        if not has_lightpink(pbs_path):
            continue

        # Find corresponding BTN file
        btn_path = os.path.join(btn_dir, f"{filename}.btn")
        if not os.path.exists(btn_path):
            print(f"BTN not found: {filename}")
            not_found += 1
            continue

        # Update gib-works to false
        if update_gib_works(btn_path, False):
            print(f"Updated: {filename}.btn -> gib-works: false")
            updated += 1
        else:
            skipped += 1

    print(f"\nDone: {updated} updated, {skipped} already correct, {not_found} not found")

if __name__ == "__main__":
    main()
