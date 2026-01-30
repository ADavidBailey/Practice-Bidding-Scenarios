#!/usr/bin/env python3
"""
Remove button-width and button-color metadata from BTN files.
These should be driven by the layout file, not stored in BTN files.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PROJECT_ROOT

def remove_style_metadata(btn_path):
    """Remove button-width and button-color lines from BTN file."""
    with open(btn_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    changed = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# button-width:') or stripped.startswith('# button-color:'):
            changed = True
            continue
        new_lines.append(line)

    if changed:
        with open(btn_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False


def main():
    btn_dir = os.path.join(PROJECT_ROOT, "btn")

    updated = 0
    for filename in sorted(os.listdir(btn_dir)):
        if not filename.endswith('.btn'):
            continue

        btn_path = os.path.join(btn_dir, filename)
        if remove_style_metadata(btn_path):
            print(f"Cleaned: {filename}")
            updated += 1

    print(f"\nDone: {updated} files cleaned")


if __name__ == "__main__":
    main()
