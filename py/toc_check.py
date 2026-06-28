#!/usr/bin/env python3
"""toc_check.py — verify coaching-non-rotated/toc.json covers every lesson.

bridge-classroom's "David Bailey Scenarios" collection live-reads this repo's
``coaching-non-rotated/`` straight from GitHub raw on ``main``: it fetches
``toc.json`` for the lesson list, then each ``<id>.pbn`` by filename. So the
toc IS the integration seam — a lesson PBN with no toc entry never appears in
BC, and a toc entry with no PBN is a dead link.

This guard keeps the two in lock-step. It reports any ``*.pbn`` missing from the
toc and any toc id with no matching PBN, and exits non-zero on either. Run from
the project root:

    python3 -P py/toc_check.py        # report drift, exit 1 if any

(``-P`` keeps py/'s ``select.py`` from shadowing the stdlib.)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COACHING_DIR = ROOT / "coaching-non-rotated"
TOC = COACHING_DIR / "toc.json"


def main():
    toc = json.loads(TOC.read_text())
    toc_ids = [l["id"] for c in toc["categories"] for l in c["lessons"]]
    pbn_ids = sorted(p.stem for p in COACHING_DIR.glob("*.pbn"))

    dup = sorted({i for i in toc_ids if toc_ids.count(i) > 1})
    missing = [p for p in pbn_ids if p not in toc_ids]   # PBN with no toc entry
    dead = [i for i in toc_ids if i not in pbn_ids]       # toc entry with no PBN

    print(f"toc lessons: {len(toc_ids)}  |  pbn files: {len(pbn_ids)}")
    if dup:
        print(f"  DUPLICATE toc ids: {dup}")
    if missing:
        print(f"  PBN missing from toc (won't show in BC): {missing}")
    if dead:
        print(f"  toc id with no PBN (dead link): {dead}")
    if not (dup or missing or dead):
        print("  OK — toc and PBN set are in lock-step.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
