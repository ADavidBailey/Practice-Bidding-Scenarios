#!/usr/bin/env python3
"""Audit coaching prose for fit/support claims that contradict the actual hands.

The bug class (issue batch 2026-06-24, FSF #105/#108/#109): coaching prose that
asserts an "eight-card fit" or "<n>-card <suit> support" the dealt hands don't
have — typically when *responder* rebids their own long major and the prose
mislabels it as opener showing support.

Heuristic + hand-truth check. Negated/asking contexts ("denying three-card
support", "no eight-card fit", "asks for ... support?", "never guaranteed") are
excluded. Run over coaching-curated/ (the staging copy).

This is a SCREENING audit, not a CI gate: a hit means "a human should look",
because "opener genuinely has N-card support for partner's suit" and "responder
mislabels a rebid of their own suit as support" can't be told apart without
parsing the auction. Exit is non-zero when there are hits so they're noticeable;
adjudicate each against the dealt hands before editing.

    python3 -P py/check_fit_claims.py [Scenario ...]

With no args, scans every bidding scenario (those with [BID] markers).
Known-acceptable hits (verified 2026-06-24): Negative_Double B328 (opener really
holds 4 spades; responder's negative double is the light side).
"""
import re, sys, glob, os

SUIT = {'spade': 0, 'heart': 1, 'diamond': 2, 'club': 3}
NUM = {'two': 2, 'three': 3, 'four': 4}
ROOT = os.path.join(os.path.dirname(__file__), '..')

# negation / hypothetical / asking context that makes a claim NOT a positive assertion
NEG = re.compile(
    r'\b(lack\w*|without|no|never|not|none|cannot|can\'?t|could\s*n\'?t|deny|denies|denied|denying|'
    r'unable|short|doubleton|singleton|asks?|asking|describe\w*|clarif\w*|whether|reveal\w*|'
    r'searching|hunting|guaranteed|promise\w*|for)\b', re.I)


def lengths(deal):
    hands = deal.split(':', 1)[1].split()
    out = {}
    for seat, h in zip('NESW', hands):
        out[seat] = [len(x) for x in h.split('.')]
    return out


def scan_file(path):
    scn = os.path.basename(path)[:-4]
    txt = open(path).read()
    if '[BID ' not in txt:
        return []                       # play scenario, no step-0 bid prose
    hits = []
    for m in re.finditer(r'\[Board "(\d+)"\].*?\[Deal "(N:[^"]+)"\].*?(\{[^{}]*\[BID.*?\})\n', txt, re.S):
        board, deal, prose = m.groups()
        L = lengths(deal)
        ns = [L['N'][i] + L['S'][i] for i in range(4)]

        for mm in re.finditer(r'eight-card fit', prose):
            pre = prose[max(0, mm.start() - 55):mm.start()]
            post = prose[mm.end():mm.end() + 30]      # "...fit is never guaranteed"
            if NEG.search(pre) or NEG.search(post):
                continue
            if not any(x >= 8 for x in ns):
                hits.append((scn, board, "claims 'eight-card fit'", "max N-S fit %d" % max(ns)))

        for mm in re.finditer(r'(two|three|four)-card (spade|heart|diamond|club) support', prose):
            pre = prose[max(0, mm.start() - 55):mm.start()]
            post = prose[mm.end():mm.end() + 3]
            if NEG.search(pre) or '?' in post:
                continue
            n, suit = NUM[mm.group(1)], SUIT[mm.group(2)]
            comb = ns[suit]
            supporter = min(L['N'][suit], L['S'][suit])   # the side that would be "supporting"
            if comb < 8 or supporter < n:
                hits.append((scn, board, "claims '%s'" % mm.group(0),
                             "N-S %s=%d (N=%d S=%d)" % (mm.group(2), comb, L['N'][suit], L['S'][suit])))
    return hits


def main(argv):
    if argv:
        files = [os.path.join(ROOT, 'coaching-curated', a + '.pbn') for a in argv]
    else:
        files = sorted(glob.glob(os.path.join(ROOT, 'coaching-curated', '*.pbn')))
    all_hits = []
    for f in files:
        if os.path.exists(f):
            all_hits.extend(scan_file(f))
    if not all_hits:
        print("fit-claim audit: clean")
        return 0
    cur = None
    for scn, board, claim, info in all_hits:
        if scn != cur:
            print("###", scn)
            cur = scn
        print(f"  B{board}: {claim} but {info}")
    print(f"\n{len(all_hits)} suspect claim(s)")
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
