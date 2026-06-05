#!/usr/bin/env python3
"""select.py — select boards from an annotated bba-curated PBN by Curate tags.

The successor to the auction-filter regex: a simple, deterministic filter
over the curation verdicts embedded in bba-curated/<scenario>.pbn.

Query terms (all must hold; values match words in the tag, OR within a term
via comma):

  bidding=textbook            CurateBidding tier
  bidding=textbook,standard   either tier
  declarer=hold-up            CurateDeclarer contains the word (tier or theme)
  defense=opening-lead-nt     CurateDefense contains the word
  class=intended              CurateClass
  diff<=2  diff=3  diff>=4    CurateDifficulty

Usage:
  python3 py/select.py Basic_NT "bidding=textbook" -n 30
  python3 py/select.py Basic_NT "declarer=count-winners" "diff<=2" -n 12 -o lesson.pbn

Without -o, prints the selected board numbers and a count. With -o, writes a
plain lesson PBN (Curate tags kept; strip with --strip).
"""
import sys, os, re
# Append (not insert(0,…)) so py/ sits at the END of sys.path: `curate` still
# resolves (it lives only here), but stdlib `select` keeps priority over this
# very file when endplay lazily pulls in subprocess. See
# reference_py_select_shadows_stdlib.
sys.path.append(os.path.dirname(__file__))
from curate import split_boards, tag

KEYS = {'class', 'bidding', 'declarer', 'defense'}


def curate_block(ch):
    """Parse the {Curate ...} comment block into a dict of key -> value."""
    m = re.search(r'\{Curate\n(.*?)\n\}', ch, flags=re.S)
    if not m: return {}
    d = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            d[k.strip()] = v.strip()
    return d


def matches(ch, term):
    m = re.match(r'([\w-]+)\s*(<=|>=|=)\s*(.+)', term)
    if not m:
        sys.exit(f"bad term: {term}")
    key, op, val = m.group(1), m.group(2), m.group(3).strip()
    blk = curate_block(ch)
    if not blk: return False
    if key == 'diff':
        d = blk.get('difficulty')
        if d is None: return False
        d, v = int(d), int(val)
        return d <= v if op == '<=' else d >= v if op == '>=' else d == v
    if key not in KEYS:
        sys.exit(f"unknown key: {key} (use {', '.join(sorted(KEYS))}, diff)")
    content = blk.get(key)
    if content is None: return False
    words = content.split()
    return any(v.strip() in words for v in val.split(','))


def main():
    args = [a for a in sys.argv[1:]]
    scn, terms, n, out, strip = None, [], None, None, False
    i = 0
    while i < len(args):
        a = args[i]
        if a == '-n': n = int(args[i+1]); i += 2
        elif a == '-o': out = args[i+1]; i += 2
        elif a == '--strip': strip = True; i += 1
        elif scn is None: scn = a; i += 1
        else: terms.append(a); i += 1
    if not scn or not terms:
        sys.exit(__doc__)
    path = f"bba-curated/{scn}.pbn"
    sel = [ch for ch in split_boards(path) if all(matches(ch, t) for t in terms)]
    total = len(sel)
    if n: sel = sel[:n]
    if out:
        text = "".join(sel)
        if strip:
            text = re.sub(r'\{Curate\n.*?\n\}\n', '', text, flags=re.S)
        open(out, "w").write(text)
        print(f"{len(sel)} boards (of {total} matching) -> {out}")
    else:
        boards = [tag(ch, 'Board') for ch in sel]
        print(f"{len(sel)} boards (of {total} matching): {' '.join(boards)}")


if __name__ == "__main__":
    main()
