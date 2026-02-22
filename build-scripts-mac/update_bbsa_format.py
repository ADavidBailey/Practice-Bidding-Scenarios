#!/usr/bin/env python3
"""
Update old-format .bbsa files to the latest format.

Uses 21GF-DEFAULT.bbsa as the canonical template for key order and names.
Maps old key names to new ones, preserves values, adds missing keys with
DEFAULT's values (not 0) so BBA behavior matches the internal defaults.

Usage:
    python3 update_bbsa_format.py           # Update all active bbsa files
    python3 update_bbsa_format.py --dry-run # Show what would change
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BBSA_DIR = os.path.join(PROJECT_ROOT, "bbsa")

# Old key name → new key name(s) mapping
# When mapping to multiple keys, all get the same value
KEY_MAPPINGS = {
    "Gerber only for 1NT and 2NT openings": ["Gerber only for NT openings"],
    "Minor Suit Stayman after 1NT": ["1N-2S Minor Suit Stayman"],
    "Minor Suit Transfers after 1NT": ["1N-2S transfer to clubs", "1N-3C transfer to diamonds"],
    "Puppet Stayman after 2NT": ["2N-3C Puppet Stayman"],
    "Puppet Stayman": ["2N-3C Puppet Stayman"],
    "Splinter 1N-3D": ["1N-3D splinter"],
    "Weak Jump Shifts": ["Weak Jump Shifts 2", "Weak Jump Shifts 3"],
    "Lavinthal on void": ["Lavinthal from void", "Lavinthal to void"],
    "Direct Jump Cuebid": [],  # drop
    "Canape style": [],  # drop (Precision-only, always 0)
    "Western cue bid": [],  # drop (Precision-only, always 0)
    "1D opening to 18 HCP": [],  # drop (Precision-only, always 0)
    "Reverse style": [],  # drop (Precision-only, always 0)
}


def read_canonical_keys(filepath):
    """Read the canonical key order from DEFAULT."""
    keys = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if " = " not in line:
                continue
            key = line.rsplit(" = ", 1)[0]
            if key == "Not defined" or key == "Opponent type":
                continue
            keys.append(key)
    return keys


def parse_bbsa(filepath):
    """Parse a bbsa file into {key: value} dict."""
    settings = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if " = " not in line:
                continue
            key, val = line.rsplit(" = ", 1)
            if key == "Not defined":
                continue
            settings[key] = val.strip()
    return settings


def write_bbsa(filepath, canonical_keys, settings, default_settings):
    """Write a bbsa file in canonical format.
    Missing settings inherit from default_settings (not 0)."""
    lines = []
    named_count = 0

    # System type first
    lines.append(f"System type = {settings.get('System type', '0')}")
    named_count += 1

    # All canonical keys (excluding System type)
    for key in canonical_keys:
        if key == "System type":
            continue
        val = settings.get(key, default_settings.get(key, "0"))
        lines.append(f"{key} = {val}")
        named_count += 1

    # Opponent type last line is always line 258
    # Pad with "Not defined = 0" to reach 257 named lines
    while named_count < 257:
        lines.append("Not defined = 0")
        named_count += 1

    lines.append("Opponent type = 0")
    lines.append("")  # trailing newline

    with open(filepath, "w") as f:
        f.write("\n".join(lines))


def map_settings(old_settings, canonical_keys):
    """Map old-format settings to canonical keys."""
    new_settings = {}

    for old_key, val in old_settings.items():
        if old_key == "Opponent type":
            new_settings["Opponent type"] = val
            continue

        if old_key in KEY_MAPPINGS:
            for new_key in KEY_MAPPINGS[old_key]:
                # Only set if not already set by a direct key
                if new_key not in new_settings:
                    new_settings[new_key] = val
        elif old_key in canonical_keys or old_key == "System type":
            new_settings[old_key] = val
        else:
            # Key not in canonical list and no mapping - warn
            print(f"    WARNING: Unknown key '{old_key}' = {val} (dropped)")

    return new_settings


def main():
    dry_run = "--dry-run" in sys.argv

    # Read canonical keys and values from DEFAULT
    default_path = os.path.join(BBSA_DIR, "21GF-DEFAULT.bbsa")
    canonical_keys = read_canonical_keys(default_path)
    default_settings = parse_bbsa(default_path)
    print(f"Canonical format: {len(canonical_keys)} named settings")

    # Process all active bbsa files
    bbsa_files = sorted(
        f for f in os.listdir(BBSA_DIR)
        if f.endswith(".bbsa") and not os.path.isdir(os.path.join(BBSA_DIR, f))
    )

    for filename in bbsa_files:
        filepath = os.path.join(BBSA_DIR, filename)
        old_settings = parse_bbsa(filepath)

        # Check if any old-format keys exist
        old_keys = [k for k in old_settings if k in KEY_MAPPINGS]
        missing_keys = [k for k in canonical_keys if k not in old_settings and
                        k not in [nk for ok in old_settings if ok in KEY_MAPPINGS
                                  for nk in KEY_MAPPINGS[ok]]]

        # Count current lines
        with open(filepath, "r") as f:
            content = f.read()
        line_count = content.strip().count("\n") + 1

        needs_update = bool(old_keys) or bool(missing_keys) or line_count != 258

        if not needs_update:
            print(f"  {filename}: OK (already up to date)")
            continue

        print(f"  {filename}:")
        if old_keys:
            print(f"    Old keys to map: {old_keys}")
        if missing_keys:
            missing_with_defaults = [k for k in missing_keys if k not in
                                     [nk for ok in old_settings if ok in KEY_MAPPINGS
                                      for nk in KEY_MAPPINGS.get(ok, [])]]
            if missing_with_defaults:
                print(f"    Missing keys to add (from DEFAULT): {len(missing_with_defaults)}")

        if dry_run:
            continue

        # Map old settings to canonical format
        mapped = map_settings(old_settings, canonical_keys)
        write_bbsa(filepath, canonical_keys, mapped, default_settings)
        print(f"    Updated to {len(canonical_keys)} named settings + padding")

    if dry_run:
        print("\n(Dry run - no files modified)")


if __name__ == "__main__":
    main()
