#!/usr/bin/env python3
"""suit_tricks.py — single-suit double-dummy trick counts with KNOWN cards.

Used by the play-coaching pipeline to ground the prose in verified numbers
(so the generating subagent narrates facts instead of counting tricks itself,
which is where it slips — cf. the board-1 "four spades" miscount).

All four hands are known, so this is exact double-dummy, not a combinatorial
estimate. Seat order N-E-S-W is respected (positional finesses matter). The
"unlimited entries" model is used: whichever side wins a trick may lead the
next from either of its two hands (declarer's side maximises NS tricks,
defenders minimise).

  ranks: 2..14 (J=11 Q=12 K=13 A=14)
  seats: 0=N 1=E 2=S 3=W ; NS = {0,2}

API:
  suit_tricks(holdings) -> max NS tricks in the suit played in isolation
      holdings: {0:set,1:set,2:set,3:set} of ranks (one suit)
  top_tricks(ns_ranks, opp_ranks) -> immediate cash-out winners (consecutive
      top honours NS holds from the ace down)
  trick_map(hands) -> per-suit {top, establishable, source?} for a full deal
      hands: {'N':[S,H,D,C], ...} each a rank-string like 'KQ762'
"""
from functools import lru_cache

RMAP = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}
NS = (0, 2)

def _ranks(s):
    return frozenset(RMAP[c] for c in s)

@lru_cache(maxsize=None)
def _solve(hands, leader):
    """hands: tuple of 4 frozensets (N,E,S,W). leader: seat 0..3.
    Returns max NS tricks from here (double dummy, unlimited entries)."""
    if not any(hands):
        return 0
    order = [(leader + i) % 4 for i in range(4)]

    def play(idx, plays, hands_cur):
        # plays: dict seat->rank (or absent if void). Resolve when 4 decided.
        if idx == 4:
            followed = {s: r for s, r in plays.items() if r is not None}
            winner = max(followed, key=lambda s: followed[s])
            new = list(hands_cur)
            for s, r in followed.items():
                new[s] = new[s] - {r}
            new = tuple(new)
            ns_won = 1 if winner in NS else 0
            # next leader chosen by the winning side (entry assumption)
            side = NS if winner in NS else (1, 3)
            opts = [s for s in side if new[s]]
            if not opts:
                opts = [s for s in side]  # both void -> suit dead; recurse ends
            sub = [ns_won + _solve(new, s) for s in opts]
            return max(sub) if winner in NS else min(sub)
        seat = order[idx]
        if not hands_cur[seat]:
            return play(idx + 1, {**plays, seat: None}, hands_cur)
        results = [play(idx + 1, {**plays, seat: c}, hands_cur) for c in hands_cur[seat]]
        return max(results) if seat in NS else min(results)

    return play(0, {}, hands)

def suit_tricks(holdings):
    hands = tuple(frozenset(holdings.get(i, frozenset())) for i in range(4))
    # NS may open the suit from either hand; defenders never want to lead it,
    # but with unlimited entries declarer controls the first lead.
    starts = [s for s in NS if hands[s]] or [0]
    return max(_solve(hands, s) for s in starts)

def top_tricks(ns_ranks, opp_ranks):
    """Immediate winners: consecutive top cards NS holds from the ace down."""
    n = 0
    r = 14
    ns = set(ns_ranks)
    while r >= 2 and r in ns:
        n += 1
        r -= 1
    return n

def trick_map(hands):
    """Per-suit analysis for a NT deal. hands: {'N':[S,H,D,C],...} rank strings.
    Returns {suit_letter: {top, establishable}} plus 'source' = the suit giving
    the most establishable-over-top tricks (the development suit)."""
    SUITS = ['S', 'H', 'D', 'C']
    out = {}
    best_dev = (-1, None)
    for i, su in enumerate(SUITS):
        hold = {0: _ranks(hands['N'][i]), 1: _ranks(hands['E'][i]),
                2: _ranks(hands['S'][i]), 3: _ranks(hands['W'][i])}
        est = suit_tricks(hold)
        ns_ranks = hold[0] | hold[2]
        opp_ranks = hold[1] | hold[3]
        # immediate winners = consecutive top honours, but never more than the
        # suit can ever yield (both NS hands follow each trick, so a long 5-5
        # fit cashes only 5 even with eight honours in a row).
        top = min(top_tricks(ns_ranks, opp_ranks), est)
        out[su] = {'top': top, 'establishable': est, 'ns_len': len(ns_ranks)}
        dev = est - top
        if dev > best_dev[0] and est > 0:
            best_dev = (dev, su)
    return {'suits': out, 'development_suit': best_dev[1]}

if __name__ == "__main__":
    # Unit tests
    def ss(d):
        return suit_tricks({k: _ranks(v) for k, v in d.items()})
    # AQ opposite xx, K onside (East, before South) -> 2 tricks
    print("AQ/xx K onside  :", ss({2: 'AQ', 0: '32', 1: 'K4', 3: '65'}), "(expect 2)")
    # AQ opposite xx, K offside (West) -> 1 trick
    print("AQ/xx K offside :", ss({2: 'AQ', 0: '32', 3: 'K4', 1: '65'}), "(expect 1)")
    # Board 1 suits (S declarer=2, N=0, E=1, W=3)
    b1 = {'N': 'J4.T42.AQ6.QJ875'.split('.'),
          'E': 'A953.93.J432.A62'.split('.'),
          'S': 'KQ762.A87.K75.KT'.split('.'),
          'W': 'T8.KQJ65.T98.943'.split('.')}
    tm = trick_map(b1)
    for su in 'SHDC':
        print(f"  {su}: {tm['suits'][su]}")
    print("  development_suit:", tm['development_suit'], "(expect C — the KQJT source)")
