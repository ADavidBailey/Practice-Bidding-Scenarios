#!/usr/bin/env python3
"""annotate.py — write Curate tags into an annotated PBN (bba-curated/<scn>.pbn).

Joins bba/<scn>.pbn boards with the Layer B verdicts in
bba-curated/<scn>-graded.json (by deal_hash) and inserts one {Curate ...}
comment block before each board's [Auction] section — same house style as
the existing {Shape}/{HCP}/{Losers} blocks, ignored by all PBN consumers
(verified: endplay parses annotated files unchanged). py/select.py filters
on the block.

Block written per board:
  {Curate
  class: intended|interference|continuation|bba-disagreed|regex-strict
  difficulty: 1..5
  bidding: tier
  also-ok: 1S 2C            (judgment boards only)
  bidding-note: ...
  declarer: tier theme...
  declarer-note: ...
  defense: tier theme...
  defense-note: ...
  }

Usage: python3 py/annotate.py Basic_NT [...]
"""
import sys, os, re, json
# Append (not insert(0,…)) so py/ sits at the END of sys.path: `curate` still
# resolves (it lives only here), but stdlib modules keep priority — notably
# `select`, which py/select.py would otherwise shadow when endplay lazily
# pulls in subprocess. See reference_py_select_shadows_stdlib.
sys.path.append(os.path.dirname(__file__))
from curate import split_boards, tag, deal_hash


def q(s):
    return (s or "").replace('}', ')').replace('{', '(')


def board_tags(v):
    """One {Curate ...} comment block, house style (cf. {Shape}/{HCP})."""
    lines = ['{Curate',
             f'class: {v["auction_class"]}',
             f'difficulty: {v["difficulty"]}']
    b = v['bidding']
    lines.append(f'bidding: {b["tier"]}')
    if b.get('also_ok'):
        lines.append(f'also-ok: {" ".join(b["also_ok"])}')
    if b.get('note'):
        lines.append(f'bidding-note: {q(b["note"])}')
    for key in ('declarer', 'defense'):
        d = v[key]
        lines.append(f'{key}: {" ".join([d["tier"]] + d.get("themes", []))}')
        if d.get('note'):
            lines.append(f'{key}-note: {q(d["note"])}')
    return lines + ['}']


def annotate(scn):
    graded = json.load(open(f"bba-curated/{scn}-graded.json"))
    by_hash = {v['deal_hash']: v for v in graded['verdicts']}
    out, missing = [], 0
    for ch in split_boards(f"bba/{scn}.pbn"):
        d = tag(ch, 'Deal')
        v = by_hash.get(deal_hash(d)) if d else None
        if v is None:
            missing += 1; out.append(ch); continue
        ins = "\n".join(board_tags(v)) + "\n"
        m = re.search(r'^\[Auction ', ch, flags=re.M)
        if m:
            ch = ch[:m.start()] + ins + ch[m.start():]
        else:
            ch = ch.rstrip() + "\n" + ins + "\n"
        out.append(ch)
    path = f"bba-curated/{scn}.pbn"
    with open(path, "w") as f:
        f.write("".join(out))
    print(f"{scn}: {len(out)} boards annotated -> {path}"
          + (f" ({missing} boards had no verdict)" if missing else ""))


if __name__ == "__main__":
    for scn in (sys.argv[1:] or ['Basic_NT']):
        annotate(scn)
