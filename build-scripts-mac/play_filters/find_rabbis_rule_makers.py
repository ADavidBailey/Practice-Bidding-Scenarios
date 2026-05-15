#!/usr/bin/env python3
"""
Filter bba/Rabbis_Rule.pbn for deals where:
  - Contract is 4S
  - Declarer is South
  - Declarer makes (Result >= 10 tricks)

The dealer constraints already place West's stiff K of diamonds and
East's heart KQ threat, so a making 4S means the safety play (cash the
A, drop the stiff K) was the line.

Output: bba/Found_Rabbis_Rule.pbn
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO_ROOT / "bba" / "Rabbis_Rule.pbn"
OUTPUT = REPO_ROOT / "bba" / "Found_Rabbis_Rule.pbn"


def main():
    text = SOURCE.read_text()
    boards = text.split("[Event")
    header = ""  # the "[Event ..." prefix is split off, so re-add it
    kept = []
    for raw in boards[1:]:
        contract_m = re.search(r'\[Contract "(\S+)"\]', raw)
        declarer_m = re.search(r'\[Declarer "(\S+)"\]', raw)
        result_m = re.search(r'\[Result "(\d+)"\]', raw)
        if not (contract_m and declarer_m and result_m):
            continue
        if contract_m.group(1) != "4S": continue
        if declarer_m.group(1) != "S": continue
        if int(result_m.group(1)) < 10: continue
        kept.append("[Event" + raw)

    # Renumber boards 1..N
    out_parts = []
    for i, raw in enumerate(kept, start=1):
        renumbered = re.sub(r'\[Board "\d+"\]', f'[Board "{i}"]', raw, count=1)
        out_parts.append(renumbered)
    OUTPUT.write_text("".join(out_parts))
    print(f"Read {len(boards)-1} deals from {SOURCE}")
    print(f"Kept {len(kept)} makers (4S by S, result >= 10)")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
