#!/usr/bin/env python3
"""auction_diff.py — find boards whose BBA auction changed after a
convention-card update, so Layer B only re-grades what actually changed.

Compares the working-tree bba/<scn>.pbn against the committed version
(git HEAD), joining boards by deal_hash (deals are seed-stable; only
auctions/contracts move). Emits a summary and writes the changed hashes to
bba-curated/.progress/<scn>-regrade.json for the regrade step.

Usage: python3 py/auction_diff.py [--base <ref>] Basic_NT [...]
  --base defaults to HEAD. Pass an earlier commit (e.g. the pre-card-change
  parent) when the regenerated bba/ files are already committed to HEAD.
"""
import sys, os, re, json, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from curate import split_boards, tag, deal_hash


def boards_from_text(raw):
    parts = re.split(r'(?=^\[Event )', raw, flags=re.M)
    out = {}
    for ch in parts:
        if not ch.startswith('[Event'): continue
        d = tag(ch, 'Deal')
        if not d: continue
        m = re.search(r'\[Auction "(\w)"\]\s*\n((?:[^\[{][^\n]*\n?)*)', ch)
        auction = " ".join(m.group(2).split()) if m else None
        out[deal_hash(d)] = {'board': tag(ch, 'Board'), 'auction': auction,
                             'contract': tag(ch, 'Contract'),
                             'declarer': tag(ch, 'Declarer')}
    return out


def diff(scn, base='HEAD'):
    path = f"bba/{scn}.pbn"
    old_raw = subprocess.run(['git', 'show', f'{base}:{path}'],
                             capture_output=True, text=True).stdout
    if not old_raw:
        print(f"{scn}: no {base} version of {path}; skipping"); return
    old = boards_from_text(old_raw)
    new = boards_from_text(open(path, encoding='utf-8', errors='replace').read())
    changed, missing = [], 0
    for h, n in new.items():
        o = old.get(h)
        if o is None:
            missing += 1; changed.append(h); continue
        if (n['auction'], n['contract'], n['declarer']) != \
           (o['auction'], o['contract'], o['declarer']):
            changed.append(h)
    os.makedirs("bba-curated/.progress", exist_ok=True)
    json.dump(changed, open(f"bba-curated/.progress/{scn}-regrade.json", "w"))
    print(f"{scn}: {len(new)} boards, {len(changed)} changed "
          f"({missing} new deals), {len(new)-len(changed)} verdicts reusable "
          f"-> .progress/{scn}-regrade.json")
    # show a few examples
    shown = 0
    for h in changed:
        o, n = old.get(h), new[h]
        if o and shown < 5:
            print(f"  b{n['board']}: {o['contract']}/{o['declarer']} [{o['auction']}]")
            print(f"      -> {n['contract']}/{n['declarer']} [{n['auction']}]")
            shown += 1


if __name__ == "__main__":
    # Optional baseline ref: --base <ref> (default HEAD). Use this when the
    # regenerated bba/ files have already been committed, so the pre-change
    # auctions live in an earlier commit rather than the working tree.
    args = sys.argv[1:]
    base = 'HEAD'
    if '--base' in args:
        i = args.index('--base'); base = args[i + 1]; del args[i:i + 2]
    for scn in (args or ['Basic_NT']):
        diff(scn, base)
