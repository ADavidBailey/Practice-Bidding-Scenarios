#!/usr/bin/env python3
"""trump_tricks.py — trick analysis for SUIT contracts (the trump-aware
counterpart of suit_tricks.trick_map, which is notrump-only).

Why a separate module: suit_tricks.trick_map counts each suit in isolation and
picks a `development_suit` — correct for notrump, but wrong for a trump contract,
where (a) the trump suit itself is a trick source whose length lives in two
hands, (b) side-suit "winners" can be RUFFED away, and (c) extra tricks come
from RUFFING declarer's losers in the short trump hand, not only from
establishing length. Feeding the NT map to the 8 suit play scenarios
(Play_Top_Tricks, Play_Top_Tricks_Suit, Rabbis_Rule, Suit_Promotion,
Finesse_Simple, Endplay_3rd_Round_Strip, Side_Suit_Ruff_Before_Trump,
To_Finesse_Or_Not_To_Finesse / Two_Way_Finesse) miscounts the contract.

What is VERIFIED (state these as fact in coaching):
  - `total`     declarer's exact double-dummy trick count in the trump strain
                (endplay calc_dd_table). The hard cap the narrative reconciles to.
  - `dd_losers` 13 - total (exact).
  - per-suit `top` / `establishable` and trump `isolated_tricks` — exact
    single-suit double-dummy (suit_tricks), seat-aware so positional finesses
    are already resolved.

What is DERIVED planning guidance (a structural decomposition to ground the
PLAN prose — clamped to be consistent with `total`, but heuristic, not a
second source of truth):
  - `ruffs_in_short_hand`  extra ruffing tricks the SHORT trump hand can take.
  - `sure_tricks`          trump winners + uncashable-proof side top winners.
  - `develop`              total - sure_tricks (tricks still to find: ruff /
                           length / finesse).

Assumes declarer's side is North/South (every curated play board is seated
South — same assumption suit_tricks.trick_map already makes). `total` is correct
for any declarer; only the N/S decomposition is skipped for an E/W declarer.

API:
  trump_trick_map(hands, trumps, declarer, deal_str=None) -> dict
      hands:    {'N':[S,H,D,C], ...} rank-strings (curate.hands output)
      trumps:   trump suit letter 'S'/'H'/'D'/'C'
      declarer: declaring seat 'N'/'E'/'S'/'W'
      deal_str: canonical PBN deal string for the authoritative DD total; if
                None it is rebuilt from `hands` in "N:" order.
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))
from suit_tricks import suit_tricks, top_tricks, _ranks
from endplay.types import Deal, Denom, Player
from endplay.dds import calc_dd_table

SUITS = ['S', 'H', 'D', 'C']
SIDX = {'S': 0, 'H': 1, 'D': 2, 'C': 3}
DEN = {'S': Denom.spades, 'H': Denom.hearts, 'D': Denom.diamonds,
       'C': Denom.clubs, 'N': Denom.nt}
PL = {'N': Player.north, 'E': Player.east, 'S': Player.south, 'W': Player.west}
PART = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
HONORS = ['A', 'K', 'Q', 'J', 'T']

_dd_cache = {}


def _deal_str(hands):
    return "N:" + " ".join('.'.join(hands[s]) for s in ('N', 'E', 'S', 'W'))


def _dd_total(deal_str, trumps, declarer):
    t = _dd_cache.get(deal_str)
    if t is None:
        t = calc_dd_table(Deal(deal_str))
        _dd_cache[deal_str] = t
    return t[DEN[trumps], PL[declarer]]


def _holding(hands, si):
    """Single-suit holdings keyed 0=N 1=E 2=S 3=W (suit_tricks convention)."""
    return {0: _ranks(hands['N'][si]), 1: _ranks(hands['E'][si]),
            2: _ranks(hands['S'][si]), 3: _ranks(hands['W'][si])}


def _missing(hands, si):
    """Outstanding honours (A K Q J T) the opponents hold in suit si."""
    ns = set(hands['N'][si]) | set(hands['S'][si])
    return [h for h in HONORS if h not in ns]


def trump_trick_map(hands, trumps, declarer, deal_str=None):
    trumps = trumps.upper()
    ti = SIDX[trumps]
    if deal_str is None:
        deal_str = _deal_str(hands)
    total = _dd_total(deal_str, trumps, declarer)
    out = {
        'trumps': trumps,
        'declarer': declarer,
        'dummy': PART[declarer],
        'total': total,                 # AUTHORITATIVE (exact DD)
        'dd_losers': 13 - total,        # AUTHORITATIVE
    }
    # The N/S decomposition only makes sense when declarer's side is N/S
    # (suit_tricks counts max N/S tricks). total above is already correct for
    # any declarer; bail out of the decomposition otherwise.
    if declarer not in ('N', 'S'):
        out['decomposition'] = None
        return out

    decl, dummy = declarer, PART[declarer]
    # --- trump suit -------------------------------------------------------
    decl_t, dummy_t = len(hands[decl][ti]), len(hands[dummy][ti])
    long_hand = decl if decl_t >= dummy_t else dummy
    short_hand = dummy if long_hand == decl else decl
    long_t, short_t = max(decl_t, dummy_t), min(decl_t, dummy_t)
    trump_iso = suit_tricks(_holding(hands, ti))
    out['trump_suit'] = {
        'ns_len': decl_t + dummy_t,
        'decl_len': decl_t, 'dummy_len': dummy_t,
        'long_hand': long_hand, 'short_hand': short_hand, 'short_len': short_t,
        'isolated_tricks': trump_iso,       # exact single-suit DD
        'missing_honors': _missing(hands, ti),
    }
    # --- side suits -------------------------------------------------------
    side = {}
    side_top = 0
    ruffs = 0
    for su in SUITS:
        if su == trumps:
            continue
        si = SIDX[su]
        hold = _holding(hands, si)
        est = suit_tricks(hold)
        ns_ranks = hold[0] | hold[2]
        top = min(top_tricks(ns_ranks, hold[1] | hold[3]), est)
        decl_l, dummy_l = len(hands[decl][si]), len(hands[dummy][si])
        # a top winner is at risk if a defender is void/short enough to ruff
        opp_min = min(len(hands['E'][si]), len(hands['W'][si]))
        safe_top = top if opp_min >= top else opp_min  # winners cashable before a ruff
        side_top += safe_top
        # extra ruffs the SHORT trump hand can take in this side suit: it ruffs
        # once void, i.e. up to (long-hand length - short-hand length) times.
        long_l = decl_l if short_hand == dummy else dummy_l
        short_l = dummy_l if short_hand == dummy else decl_l
        suit_ruffs = max(0, long_l - short_l)
        ruffs += suit_ruffs
        side[su] = {
            'top': top, 'safe_top': safe_top, 'establishable': est,
            'length_winners': max(0, est - top), 'ns_len': decl_l + dummy_l,
            'decl_len': decl_l, 'dummy_len': dummy_l,
            'short_hand_ruffs': suit_ruffs, 'missing_honors': _missing(hands, si),
        }
    ruffs_in_short_hand = min(short_t, ruffs)   # capped by short hand's trumps
    sure = min(trump_iso + side_top, total)
    out['side_suits'] = side
    out['side_top'] = side_top
    out['ruffs_in_short_hand'] = ruffs_in_short_hand
    out['sure_tricks'] = sure
    out['develop'] = max(0, total - sure)
    return out


if __name__ == "__main__":
    # Sanity tests on real curated boards (declarer South throughout).
    sys.path.append(os.path.dirname(__file__))
    from curate import split_boards, tag, hands as parse_hands

    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SCN = ['Play_Top_Tricks', 'Play_Top_Tricks_Suit', 'Rabbis_Rule',
           'Suit_Promotion', 'Finesse_Simple', 'Endplay_3rd_Round_Strip',
           'Side_Suit_Ruff_Before_Trump', 'Two_Way_Finesse',
           'To_Finesse_Or_Not_To_Finesse']
    fails = 0
    for scn in SCN:
        path = os.path.join(ROOT, 'bba-curated', f'{scn}.pbn')
        if not os.path.exists(path):
            print(f"  {scn}: (no pbn)"); continue
        ch = split_boards(path)[0]
        deal = tag(ch, 'Deal'); con = tag(ch, 'Contract'); dec = tag(ch, 'Declarer')
        h = parse_hands(deal)
        deal_str = "N:" + " ".join('.'.join(h[s]) for s in ('N', 'E', 'S', 'W'))
        trumps = con[1]
        m = trump_trick_map(h, trumps, dec, deal_str)
        # cross-check total directly against endplay
        ref = calc_dd_table(Deal(deal_str))[DEN[trumps], PL[dec]]
        ok = (m['total'] == ref)
        inv = []
        d = m.get('decomposition', 'has')
        if dec in ('N', 'S'):
            ts = m['trump_suit']
            if not (ts['isolated_tricks'] <= ts['ns_len']):
                inv.append('trump iso>len')
            for su, s in m['side_suits'].items():
                if s['establishable'] < s['top']:
                    inv.append(f'{su} est<top')
            if not (m['sure_tricks'] <= m['total']):
                inv.append('sure>total')
        status = 'OK' if ok and not inv else 'FAIL'
        if status == 'FAIL':
            fails += 1
        line = (f"  {scn:30s} {con} by {dec}: total={m['total']} "
                f"(ref {ref}) losers={m['dd_losers']}")
        if dec in ('N', 'S'):
            line += (f" | trumps {trumps}={m['trump_suit']['isolated_tricks']}"
                     f" side_top={m['side_top']} ruffs={m['ruffs_in_short_hand']}"
                     f" sure={m['sure_tricks']} develop={m['develop']}")
        print(f"[{status}] {line}")
        if inv:
            print("         invariant breaches:", inv)
    print(f"\n{'ALL OK' if fails == 0 else str(fails)+' FAILURES'}")
