#!/usr/bin/env python3
"""Compare two .bbsa convention card files and print enabled/disabled differences.

Usage:
  bbsa_diff.py 21GF-DEFAULT.bbsa 21GF-GIB.bbsa
  bbsa_diff.py 21GF-DEFAULT 21GF-GIB           # short form (no .bbsa)
  bbsa_diff.py --all 21GF-GIB                  # compare GIB against all others

Each .bbsa file has 258 named settings of the form `Setting name = 0/1`.
"""

import sys
from pathlib import Path

BBSA_DIR = Path(__file__).parent.parent / "bbsa"

def parse_bbsa(path: Path) -> dict[str, str]:
    """Parse .bbsa file into {setting_name: value} dict, skipping 'Not defined' lines."""
    settings = {}
    for line_no, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("Not defined"):
            continue
        if "=" not in line:
            continue
        name, _, value = line.rpartition("=")
        name = name.strip()
        value = value.strip()
        if name and value in ("0", "1"):
            settings[name] = value
    return settings

def resolve_path(arg: str) -> Path:
    """Resolve a .bbsa filename, with or without extension, relative to bbsa/."""
    p = Path(arg)
    if p.suffix != ".bbsa":
        p = p.with_suffix(".bbsa")
    if not p.is_absolute():
        p = BBSA_DIR / p
    if not p.exists():
        raise SystemExit(f"Not found: {p}")
    return p

def diff(a_path: Path, b_path: Path) -> None:
    a = parse_bbsa(a_path)
    b = parse_bbsa(b_path)
    all_keys = sorted(set(a) | set(b))

    differences = []
    only_in_a = []
    only_in_b = []

    for k in all_keys:
        av = a.get(k)
        bv = b.get(k)
        if av is None:
            only_in_b.append(k)
        elif bv is None:
            only_in_a.append(k)
        elif av != bv:
            differences.append((k, av, bv))

    print(f"Comparing:")
    print(f"  A: {a_path.name}")
    print(f"  B: {b_path.name}")
    print()
    print(f"Settings in both: {len(a) & len(b) or min(len(a), len(b))}")
    print(f"Differing values: {len(differences)}")
    print()

    if differences:
        a_name = a_path.stem
        b_name = b_path.stem
        col_w = max(len(k) for k, _, _ in differences) + 2
        print(f"{'Setting':<{col_w}} {a_name:<25} {b_name:<25}")
        print("-" * (col_w + 52))
        for k, av, bv in differences:
            a_str = "enabled" if av == "1" else "disabled"
            b_str = "enabled" if bv == "1" else "disabled"
            marker = "*" if av != bv else " "
            print(f"{marker} {k:<{col_w-2}} {a_str:<25} {b_str:<25}")
    else:
        print("No differing values.")

    if only_in_a:
        print(f"\nSettings only in {a_path.name}: {only_in_a}")
    if only_in_b:
        print(f"\nSettings only in {b_path.name}: {only_in_b}")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        raise SystemExit(1)

    if args[0] == "--all":
        if len(args) != 2:
            raise SystemExit("--all requires one .bbsa file to compare against")
        target = resolve_path(args[1])
        for f in sorted(BBSA_DIR.glob("*.bbsa")):
            if f == target:
                continue
            print("=" * 70)
            diff(target, f)
            print()
        return

    if len(args) != 2:
        raise SystemExit("Provide two .bbsa filenames (or use --all <ref>)")

    a = resolve_path(args[0])
    b = resolve_path(args[1])
    diff(a, b)

if __name__ == "__main__":
    main()
