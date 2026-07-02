#!/usr/bin/env python3
"""rotate180.py — deterministically re-seat a PBN board by 180° (N<->S, E<->W).

Used to build the "other side of the table" boards for seat-alternating coaching
lessons: an opener-side deal (student = South = opener) becomes a responder-side
deal (student = South = responder) by rotating the whole table 180°. The auction
is NOT re-bid — the same calls are simply relabelled to their new seats, so this
needs no bidding engine (works while bba-cli is down).

Under a 180° rotation the partnerships map to themselves (N-S -> S-N is still N-S;
E-W -> W-E is still E-W), so vulnerability, contract strain/level, declarer's side,
result, and the NS/EW score are all unchanged. Only the individual seats swap:

  Deal      N:hN hE hS hW   ->  N:hS hW hN hE      (N<->S, E<->W)
  Dealer    S -> N, N -> S, E -> W, W -> E
  Declarer  same seat map
  Auction   header seat gets the same map; the call tokens are unchanged
  {Shape/HCP/Losers a b c d}  (per-seat N E S W) -> (c d a b)
  % <hash>  a stale BBA fingerprint -> recomputed from the rotated deal (kept in
            BBA's 28-uppercase-hex FORMAT; it's only a PBN comment, nothing keys on
            it — records key on board number, see reference_bc_board_identity...)

Rotating twice is the identity. CLI rotates every board in a file, or only the
boards whose [Board] number is in --boards:

    python3 -P py/rotate180.py in.pbn out.pbn
    python3 -P py/rotate180.py in.pbn out.pbn --boards 3,7,12
"""
import os, re, sys, hashlib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from curate import split_boards, tag, hands

FLIP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}


def _rotate_deal(deal_str):
    """N:hN hE hS hW -> N:hS hW hN hE  (always emit N-first)."""
    h = hands(deal_str)
    j = lambda seat: '.'.join(h[seat])
    return "N:" + " ".join([j('S'), j('W'), j('N'), j('E')])


def _bba_fingerprint(deal_str):
    """A stable 28-uppercase-hex fingerprint of the deal, matching the FORMAT of
    the BBA `%` comment. Deterministic; only used as a provenance comment."""
    return hashlib.sha1(deal_str.encode()).hexdigest()[:28].upper()


def _rotate_statblock(m):
    """{Name a b c d} in N E S W order -> {Name c d a b}."""
    name, vals = m.group(1), m.group(2).split()
    if len(vals) != 4:
        return m.group(0)
    n, e, s, w = vals
    return "{%s %s}" % (name, " ".join([s, w, n, e]))


def rotate_board(chunk):
    """Return the 180°-rotated copy of one PBN board chunk."""
    deal = tag(chunk, 'Deal')
    if not deal:
        return chunk
    new_deal = _rotate_deal(deal)
    out = chunk

    # % fingerprint comment (first line after [Board]) -> recompute for the new deal
    out = re.sub(r'(?m)^% [0-9A-Fa-f]+\s*$', '% ' + _bba_fingerprint(new_deal), out, count=1)

    # [Deal "..."]
    out = out.replace('[Deal "%s"]' % deal, '[Deal "%s"]' % new_deal)

    # seat-valued tags: Dealer, Declarer, Auction header
    for name in ('Dealer', 'Declarer', 'Auction'):
        v = tag(out, name)
        if v in FLIP:
            out = re.sub(r'\[' + name + r' "' + re.escape(v) + r'"\]',
                         '[%s "%s"]' % (name, FLIP[v]), out, count=1)

    # {Shape ...} {HCP ...} {Losers ...} per-seat reorder
    out = re.sub(r'\{(Shape|HCP|Losers) ([^}]*)\}', _rotate_statblock, out)
    return out


def rotate_file(src, dst, boards=None):
    chunks = split_boards(src)
    keep = set(boards) if boards else None
    outp = []
    for ch in chunks:
        bn = tag(ch, 'Board')
        outp.append(rotate_board(ch) if (keep is None or bn in keep) else ch)
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write("".join(outp))
    n = len(keep) if keep else len(chunks)
    print(f"rotate180: wrote {dst} — rotated {n}/{len(chunks)} board(s)")


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    boards = None
    for a in sys.argv[1:]:
        if a.startswith('--boards'):
            boards = set(a.split('=', 1)[1].split(',')) if '=' in a else None
    if '--boards' in sys.argv:
        i = sys.argv.index('--boards')
        boards = set(sys.argv[i + 1].split(','))
    if len(args) < 2:
        sys.exit("usage: rotate180.py in.pbn out.pbn [--boards 3,7,12]")
    rotate_file(args[0], args[1], boards)
