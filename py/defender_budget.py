#!/usr/bin/env python3
"""defender_budget.py — what declarer can KNOW / INFER about the defenders'
combined HCP and shape, for grounding play-coaching prose.

This is the HCP/shape counterpart of suit_tricks.trick_map: that module exists
because counting TRICKS by eye is where generated coaching slips; this one
exists because reasoning about the DEFENDERS' hidden cards by eye slips the
same way (over-stating how much a defender can hold, mis-placing the missing
honours, getting the rule-of-11 count wrong). The play-coaching subagent should
NARRATE these numbers, not derive them.

In the current play scenarios the opponents pass throughout (1N-...-stop), so
the only information available to declarer is:

  1. the HCP complement -- declarer + dummy are an EXACT known count, so the
     two defenders share exactly 40 - (declarer + dummy);
  2. the negative inference from silence -- if both defenders passed, neither
     holds a hand worth an overcall or a penalty double (a soft cap);
  3. the rule of eleven on a 4th-best (length) opening lead vs notrump -- which
     places exactly how many cards above the led card sit in the hidden
     defender's hand.

EXACT-FACT vs INFERENCE discipline (mirrors GENERATOR-PLAY.md's hedging rule):
  - ns_hcp / defender_hcp are EXACT and known to declarer once dummy is down --
    narrate them as fact.
  - the per-defender split (which defender holds what) and any honour placement
    are INFERENCES -- the author may use the true split to write a correctly
    DIRECTED read, but the prose must HEDGE it ("the missing 16 are split, and
    West led from length, so East likely holds the outstanding aces").

API:
  defender_budget(hands, declarer, dealer=None, auction=None, opening_lead=None)
    hands:       {'N':[S,H,D,C], 'E':..., 'S':..., 'W':...} rank-strings
                 (curate.hands() output).
    declarer:    declaring seat 'N'/'E'/'S'/'W'.
    dealer:      dealing seat (needed, with auction, for the silence inference).
    auction:     raw auction string (space-separated calls) or None.
    opening_lead: (suit_idx, rank) as returned by curate.opening_lead_vs_nt;
                 if None it is computed from the leader's hand (NT lead).
    Returns the dict documented under _build() below.
"""
import sys, os, re
sys.path.append(os.path.dirname(__file__))
from curate import hands as _parse_hands, hcp_of, opening_lead_vs_nt, _honor_sequence_top, SUITS, HCP

PARTNER = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
LHO = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
SEATS = ['N', 'E', 'S', 'W']
PIP = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
       '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
CALL_RE = re.compile(r'(?i)^(pass|x|xx|ap|\d[cdhsn]t?)$')


def _shape(seat_suits):
    """(lengths SHDC tuple, longest length)."""
    lens = tuple(len(s) for s in seat_suits)
    return lens, max(lens)


def _silent(dealer, auction, defenders):
    """True if both DEFENDER seats made only Pass calls in the auction (so
    neither could act -- no overcall, no penalty double). None if the auction
    or dealer is unknown (caller can't make the inference)."""
    if not auction or not dealer:
        return None
    calls = [t for t in auction.split() if CALL_RE.match(t)]
    di = SEATS.index(dealer)
    by_seat = {s: [] for s in SEATS}
    for j, c in enumerate(calls):
        by_seat[SEATS[(di + j) % 4]].append(c.upper())
    return all(c == 'PASS' for d in defenders for c in by_seat[d])


def _rule_of_eleven(hands, leader, opening_lead):
    """Rule of 11 on a 4th-best length lead vs notrump. Returns the placement
    of cards higher than the led card, or None when the lead is not a 4th-best
    length lead (a sequence top or a short-suit lead -- rule of 11 doesn't
    apply). Keys:
      suit, card        the led suit letter and rank
      higher_outside    cards above the led card in the other three hands
                        (= 11 - pip; the rule-of-11 number)
      higher_in_ns      of those, how many declarer + dummy can SEE
      higher_in_hidden  the remainder -- in the leader's PARTNER's hand
                        (the inference declarer cashes in on)
    """
    si, rank = opening_lead
    cards = hands[leader][si]
    # rule of 11 is valid only for a 4th-best length lead
    if _honor_sequence_top(cards) or len(cards) < 4 or cards[3] != rank:
        return None
    pip = PIP[rank]
    defending_pair = {leader, PARTNER[leader]}
    declarer_side = [s for s in SEATS if s not in defending_pair]
    others = [s for s in SEATS if s != leader]      # the three hands the rule counts
    higher_outside = sum(1 for s in others for c in hands[s][si] if PIP[c] > pip)
    higher_in_ns = sum(1 for s in declarer_side for c in hands[s][si] if PIP[c] > pip)
    return {
        'suit': SUITS[si], 'card': rank,
        'higher_outside': higher_outside,          # == 11 - pip
        'higher_in_ns': higher_in_ns,              # visible to declarer
        'higher_in_hidden': higher_outside - higher_in_ns,
    }


def _build(hands, declarer, dealer=None, auction=None, opening_lead=None):
    dummy = PARTNER[declarer]
    leader = LHO[declarer]
    rho = PARTNER[leader]                           # leader's partner (the hidden defender)
    defenders = [leader, rho]
    ns_hcp = hcp_of(hands[declarer]) + hcp_of(hands[dummy])
    defender_hcp = 40 - ns_hcp
    if opening_lead is None:
        opening_lead = opening_lead_vs_nt(hands[leader])
    def_block = {}
    for d, role in ((leader, 'lho'), (rho, 'rho')):
        lens, longest = _shape(hands[d])
        def_block[role] = {
            'seat': d, 'hcp': hcp_of(hands[d]),
            'shape': lens, 'longest': longest,
        }
    return {
        'ns_hcp': ns_hcp,                 # EXACT: declarer + dummy (fact post-lead)
        'defender_hcp': defender_hcp,     # EXACT: 40 - ns_hcp (shared ceiling)
        'defenders': def_block,           # per-defender TRUE split -> hedge in prose
        'silent': _silent(dealer, auction, defenders),
        'rule_of_11': (_rule_of_eleven(hands, leader, opening_lead)
                       if opening_lead else None),
    }


def defender_budget(hands, declarer, dealer=None, auction=None, opening_lead=None):
    return _build(hands, declarer, dealer, auction, opening_lead)


if __name__ == "__main__":
    # Tests against Play_Top_Tricks_NT (coaching-curated) boards 1 and 2.
    b1 = _parse_hands("N:T76.94.AK852.J98 Q982.J863.T3.KQT "
                      "AJ4.A7.QJ74.A652 K53.KQT52.96.743")
    r1 = defender_budget(b1, 'S', dealer='S', auction='1N Pass 2N Pass Pass Pass')
    print("board 1:", r1)
    assert r1['ns_hcp'] == 24, r1['ns_hcp']          # S16 + N8
    assert r1['defender_hcp'] == 16, r1['defender_hcp']
    assert r1['silent'] is True
    assert r1['rule_of_11'] is None                  # West leads \HK (sequence top)
    assert r1['defenders']['lho']['hcp'] == 8        # West
    assert r1['defenders']['rho']['hcp'] == 8        # East

    b2 = _parse_hands("N:972.T42.AK3.9852 QJ.J8653.642.KQJ "
                      "A86.AKQ7.987.AT6 KT543.9.QJT5.743")
    r2 = defender_budget(b2, 'S', dealer='S', auction='1N Pass Pass Pass')
    print("board 2:", r2)
    assert r2['ns_hcp'] == 24, r2['ns_hcp']          # S17 + N7
    assert r2['defender_hcp'] == 16
    # West leads \S4 (4th-best of KT543): rule of 11 -> 11-4 = 7 higher outside
    ro = r2['rule_of_11']
    assert ro and ro['suit'] == 'S' and ro['card'] == '4', ro
    assert ro['higher_outside'] == 7, ro             # N(9,7)=2 + S(A,8,6)=3 + E(Q,J)=2
    assert ro['higher_in_ns'] == 5, ro               # declarer+dummy see 5
    assert ro['higher_in_hidden'] == 2, ro           # East holds Q,J over the 4
    print("all assertions passed")
