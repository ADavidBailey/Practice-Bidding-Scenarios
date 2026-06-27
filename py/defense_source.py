#!/usr/bin/env python3
"""Shared sourcing + auction-reading for the defense-lead decks.

- Cross-corpus pool: scan all bba/*.pbn, keep NATURAL auctions (no `=N=` artificial
  alerts), rotate each so declarer = East / SOUTH is on lead, dedup.
- Auction categorise: opp_1NT / opp_suit / we_opened / competitive.
- Auction-reading (classifier B): find PARTNER's real suit (overcall or major opening;
  a 1C/1D opening is NOT a real suit) and the card to lead in it.

Run from project root:  python3 -P py/defense_source.py            (corpus report)
                        python3 -P py/defense_source.py --context competitive --examples 12
"""
import os
import sys
import re
import json
import glob
import argparse
from collections import Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # end of path: don't shadow stdlib
from defense_lead_select import (
    parse_boards, hand_suits, pretty, card_code, SEATS, IDX, SUITS,
    deal_to_dict, dict_to_deal, classify_lead, mixed_order, cc_token,
    conventional_lead_card,
)

ALERT = re.compile(r'^=\d+=?$')
SUITBID = re.compile(r'^[1-7][SHDC]$')
MAJORS = ('H', 'S')


def is_natural(auction):
    """Natural = no artificial-bid alert markers (=1=, =2= ...) in the auction."""
    return not any(ALERT.match(t) for t in auction)


def auction_calls(r):
    """[(seat, BID)] for the rotated auction, alert tokens dropped, normalised upper."""
    start = IDX[r['AuctionSeat']]
    out, i = [], 0
    for tok in r['auction']:
        if ALERT.match(tok):
            continue                       # alert belongs to the previous bid, not a turn
        b = re.sub(r'[!?]', '', tok).upper()
        b = {'P': 'PASS', 'DBL': 'X', 'DOUBLE': 'X', 'RDBL': 'XX', 'REDOUBLE': 'XX'}.get(b, b)
        out.append((SEATS[(start + i) % 4], b))
        i += 1
    return out


def categorize(r):
    """opp_1NT | opp_suit | we_opened | competitive | other."""
    calls = auction_calls(r)
    nz = [(s, b) for s, b in calls if b != 'PASS']
    if not nz:
        return 'other'
    opener, obid = nz[0]
    ns = any(s in ('N', 'S') for s, _ in nz)
    ew = any(s in ('E', 'W') for s, _ in nz)
    opp = opener in ('E', 'W')
    if opp and obid in ('1N', '1NT') and not ns:
        return 'opp_1NT'
    if opp and SUITBID.match(obid) and not ns:
        return 'opp_suit'
    if opener in ('N', 'S'):
        return 'we_opened'
    if opp and ns and ew:
        return 'competitive'
    return 'other'


def partner_real_suit(r):
    """Partner = North (leader's partner). Return (suit, kind, position) or None.

    kind: 'overcall' | 'major_open' | 'new_suit'   (a 1C/1D OPENING is NOT real -> None)
    position: 'under' (North bid the suit before declarer East spoke) | 'over'
    """
    calls = auction_calls(r)
    seq = [(i, s, b) for i, (s, b) in enumerate(calls)]
    north = [(i, b) for i, s, b in seq if s == 'N' and SUITBID.match(b)]
    if not north:
        return None
    idx, bid = north[0]
    suit = bid[1]
    first_nonpass = next((i for i, s, b in seq if b != 'PASS'), None)
    ew_before = any(s in ('E', 'W') and b != 'PASS' for i, s, b in seq if i < idx)
    if idx == first_nonpass:                      # North opened the auction
        if suit in MAJORS:
            kind = 'major_open'
        else:
            return None                           # 1C/1D opening: not a real suit
    elif ew_before:
        kind = 'overcall'                         # bid a suit after an opponent acted
    else:
        kind = 'new_suit'                         # response / new suit on our side
    east_first = next((i for i, s, b in seq if s == 'E' and b != 'PASS'), 99)
    position = 'under' if idx < east_first else 'over'
    return (suit, kind, position)


def partner_lead_card(suits, suit):
    """Card to lead in partner's suit, by South's holding (first cut; canon refines)."""
    c = suits[suit]
    if not c:
        return None                               # void: can't lead it
    if len(c) == 1:
        return card_code(suit, c[0])              # singleton: lead it
    if len(c) >= 3 and 11 <= c[0] <= 13 and c[0] - c[1] == 1 and c[1] - c[2] in (1, 2):
        return card_code(suit, c[0])              # top of a sequence
    if len(c) == 2:
        return card_code(suit, c[0])              # doubleton: top
    if c[0] == 14:                                # ace in partner's suit: never underlead it
        return card_code(suit, c[1] if c[1] == 13 else c[0])   # K from A-K, else cash the ace
    if c[0] >= 11:
        return card_code(suit, c[3] if len(c) >= 4 else c[-1])  # to an honour: low
    return card_code(suit, c[0])                  # 3+ small: top (of nothing)


def _own_sequence_suit(suits, exclude):
    """A non-excluded suit holding a 3-card or long 2-card top sequence -> suit, else None."""
    for s in SUITS:
        if s in exclude:
            continue
        c = suits[s]
        if len(c) >= 3 and 11 <= c[0] <= 13 and c[0] - c[1] == 1 and c[1] - c[2] in (1, 2):
            return s
        if len(c) >= 4 and 11 <= c[0] <= 13 and c[0] - c[1] == 1:
            return s
    return None


def classify_suit_lead(suits, trump, r):
    """Suit-contract lead per canon A (David, priority order):
    1 partner's real suit (unless 3+ small there AND you hold your own sequence),
    2 top of a sequence (3-card / 2-card-in-long / interior), 3 singleton for a ruff
    (short trumps + entry), 4 K from A-K, else judgment (SD decides).
    Underleading an ace is never produced -> it grades 'wrong'.
    """
    sides = [s for s in SUITS if s != trump]

    pr = partner_real_suit(r)                      # 1. partner's real suit
    if pr and pr[0] != trump and suits[pr[0]]:
        psuit, ph = pr[0], suits[pr[0]]
        supportive = len(ph) <= 2 or ph[0] >= 11   # doubleton/singleton, or an honour
        if supportive or not _own_sequence_suit(suits, (trump, psuit)):
            return ('partners_suit', psuit, partner_lead_card(suits, psuit), f"partner's {pr[1]} suit")
        # else: 3+ small in partner's suit AND we hold our own sequence -> lead our own

    for s in sides:                                # 2a. 3-card sequence
        c = suits[s]
        if len(c) >= 3 and 11 <= c[0] <= 13 and c[0] - c[1] == 1 and c[1] - c[2] in (1, 2):
            return ('sequence', s, card_code(s, c[0]), 'top of a sequence')
    for s in sides:                                # 2b. 2-card top sequence in a long suit
        c = suits[s]
        if len(c) >= 4 and 11 <= c[0] <= 13 and c[0] - c[1] == 1:
            return ('sequence', s, card_code(s, c[0]), 'top of a two-card sequence in your long suit')
    for s in sides:                                # 2c. interior sequence (KJT9, AJT, QT9...)
        c = suits[s]
        if len(c) >= 2 and c[0] == 14 and c[1] == 13:
            continue                               # A-K headed: lead the K (below), not interior
        for i in range(1, len(c) - 1):
            if c[i] - c[i + 1] == 1 and c[i] >= 10 and c[i - 1] - c[i] >= 2:
                return ('interior_sequence', s, card_code(s, c[i]), 'top of an interior sequence')

    has_entry = any(suits[s] and suits[s][0] == 14 for s in sides)   # an outside ace
    if len(suits[trump]) <= 3 and has_entry:       # 3. singleton for a ruff (short trumps + entry)
        for s in sides:
            if len(suits[s]) == 1 and suits[s][0] < 11:   # SMALL singleton only (never a singleton honour)
                return ('singleton', s, card_code(s, suits[s][0]), 'singleton, lead for a ruff')

    for s in sides:                                # 4. K from A-K
        c = suits[s]
        if len(c) >= 2 and c[0] == 14 and c[1] == 13:
            return ('AK', s, card_code(s, c[1]), 'King from A-K')

    return ('judgment', None, None, 'no clear-cut lead — SD decides')


def rotate_to_seat(board, target='E'):
    """Rotate so the declarer sits at `target`. target='E' -> South leads (LHO);
    target='W' -> South is third hand (North leads, East dummy)."""
    dec = board['Declarer']
    k = (IDX[target] - IDX[dec]) % 4
    old = deal_to_dict(board['Deal'])
    new = {SEATS[t]: old[SEATS[(t - k) % 4]] for t in range(4)}
    rseat = lambda s: SEATS[(IDX[s] + k) % 4]
    vul = board.get('Vulnerable', 'None')
    if k % 2 == 1:
        vul = {'NS': 'EW', 'EW': 'NS'}.get(vul, vul)
    return {'Deal': dict_to_deal(new), 'Dealer': rseat(board.get('Dealer', 'N')),
            'Declarer': target, 'Vulnerable': vul,
            'AuctionSeat': rseat(board.get('Auction', board.get('Dealer', 'N'))),
            'Contract': board['Contract'], 'Result': board.get('Result', ''),
            'auction': board['auction'], 'south': new['S'], 'deal_dict': new,
            'OriginalBoard': board['Board']}


def load_pool(files=None, natural_only=True, dedup=True, target='E'):
    """Return rotated boards (declarer=E, South on lead) with category + partner info."""
    files = files or sorted(glob.glob('bba/*.pbn'))
    seen, pool = set(), []
    for path in files:
        scn = os.path.basename(path)[:-4]
        try:
            boards = parse_boards(path)
        except Exception:
            continue
        for b in boards:
            if 'Deal' not in b or 'Declarer' not in b or 'Contract' not in b:
                continue
            if len(b['Contract']) < 2 or b['Contract'][1] not in 'NSHDC':
                continue                           # passed out / no real contract
            if natural_only and not is_natural(b['auction']):
                continue
            try:
                r = rotate_to_seat(b, target)
            except Exception:
                continue
            if dedup:
                key = (r['Deal'], r['Contract'], tuple(b['auction']))
                if key in seen:
                    continue
                seen.add(key)
            r['scn'] = scn
            r['context'] = categorize(r)
            r['strain'] = 'NT' if r['Contract'][1] == 'N' else 'suit'  # strain = 2nd char (X/XX may trail)
            pool.append(r)
    return pool


# ---------- suit-deck generation ----------

PROSE_SUIT = {
    'sequence': [
        "Lead the {C}, the top of your \\{X} sequence. Against a suit contract, touching honours make a safe, attacking lead — you knock out a high card and build a trick in your strong suit while you still hold the cards behind it.",
        "Lead the {C}. From a sequence you lead the top honour: it cannot cost, it promises the cards beneath, and it goes to work on your best suit before declarer sets up discards.",
    ],
    'singleton': [
        "Lead the {C}, your singleton \\{X}. Short in trumps with an entry on the side, attack with the singleton and hope partner can win and give you a ruff — a trick your high cards alone could never make.",
        "Lead your singleton {C}. With short trumps and an outside ace for an entry, go for the ruff: win, lead your singleton suit, and take the ruff before declarer can draw trumps.",
    ],
    'AK': [
        "Lead the {C}, the king from your A-K. Cash the king first — it keeps the lead and lets you see dummy before deciding whether to continue, switch, or look for a ruff.",
        "Lead the {C}. Leading the king from A-K is safe and informative — you hold the lead and read dummy before committing your defence.",
    ],
    'interior_sequence': [
        "Lead the {C}, the top of your interior sequence in \\{X}. With a high honour and a touching run just below it, lead the top of that run — it develops your long suit while your high card stays poised over declarer.",
        "Lead the {C}. You hold a higher honour, a gap, then a touching pair — lead the top of the inner run to attack your long \\{X} suit without burying your top card.",
    ],
    'partners_suit': [
        "Lead partner's \\{X} — the {C}. He bid a real suit, so attack it: leading partner's suit develops his tricks and is rarely wrong once he has shown length.",
    ],
    'judgment': [
        "Lead the {C}. There is no textbook stand-out here — on the balance of likely layouts this is the workmanlike choice. It is a genuine judgement call, and a couple of other leads are defensible.",
    ],
}

SUITSYMc = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣', 'N': 'NT'}


def con_words(contract):
    s = contract[1]
    return contract[0] + (SUITSYMc[s] if s == 'N' else SUITSYMc[s])


def card_escape(code):
    suit, rank = code[0], code[1:]
    return '\\' + suit + ('10' if rank == 'T' else rank)


def fmt_auction(bids):
    bids = [('Pass' if b.upper() in ('P', 'PASS') else b) for b in bids if not ALERT.match(b)]
    return '\n'.join('  '.join(f'{b:<5}' for b in bids[i:i + 4]).rstrip() for i in range(0, len(bids), 4))


def gen_prose_suit(tier, suit, card, variant):
    tmpl = PROSE_SUIT[tier]
    return tmpl[variant % len(tmpl)].format(C=card_escape(card), X=suit)


def widen_suit(suits, principled, r, trump):
    """TIGHT widening (suit contract): accept the principled card, plus a second card ONLY
    when another suit is independently a STRONG standard lead — partner's real suit, a
    sequence/interior sequence, or A-K. Found by re-running classify_suit_lead on the hand
    minus the principled suit. Singleton-ruff and judgment seconds don't widen; never a
    different card of the SAME suit (the equal-honour signal rule)."""
    psuit = principled[0]
    reduced = {s: (suits[s] if s != psuit else []) for s in SUITS}
    tier, _suit, card, _why = classify_suit_lead(reduced, trump, r)
    if card and tier in ('partners_suit', 'sequence', 'interior_sequence', 'AK'):
        return [principled, card]
    return [principled]


_RANKV = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
          '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}


def judgment_blind_ok(suits, trump, suit, card):
    """A judgment board's SD-chosen lead is kept only if a good player could choose it
    BLIND — from the bidding and their own hand, without seeing the other three. Rejects the
    'DD chose blind' leads: underleading an ace, underleading a K/Q from a short suit, or
    leading a short suit while a 5+ suit sits idle. DD then only tie-breaks AMONG
    blind-defensible leads — it is no longer the chooser. (Not applied to Major_Defense_LHO,
    whose judgment boards David has already reviewed.)"""
    sides = [s for s in SUITS if s != trump]
    c = suits[suit]
    if not c:
        return False
    val = _RANKV[card[1]]
    longest = max(len(suits[s]) for s in sides)
    if c[0] == 14 and val != 14:                  # never underlead an ace
        return False
    if c[0] >= 11 and val < c[0] and (len(c) < 4 or len(c) < longest):
        return False                              # underlead an honour only from your longest 4+ suit
    safe_long = any(s != trump and len(suits[s]) >= 4 and suits[s][0] <= 10 for s in SUITS)
    if len(c) < 4 and safe_long:                  # short lead while a safe 4+ top-of-nothing suit sits idle
        return False
    if longest >= 5 and len(c) < longest:         # prefer your own 5+ length
        return False
    return True


def emit_board(n, event, r, card, prose, accepted=None):
    con = r['Contract']
    return (
        f'[Event "{event}"]\n[Site ""]\n[Board "{n}"]\n'
        f'[North "EPBot"]\n[East "EPBot"]\n[South "EPBot"]\n[West "EPBot"]\n'
        f'[Dealer "{r["Dealer"]}"]\n[Vulnerable "{r["Vulnerable"]}"]\n'
        f'[Deal "{r["Deal"]}"]\n[Scoring "MP"]\n[Declarer "E"]\n'
        f'[Contract "{con}"]\n[Result "{r.get("Result","")}"]\n[Student "S"]\n'
        f'[Category "Defense"]\n[Difficulty "beginner"]\n[SkillPath "defense/opening_leads"]\n'
        f'[OriginalSource "{r["scn"]} board {r["OriginalBoard"]}, rotated 90 so South is on lead"]\n'
        f'[Auction "{r["AuctionSeat"]}"]\n{fmt_auction(r["auction"])}\n'
        '{[show S]\n\n'
        f'The opponents have bid to {con_words(con)} and it is your lead.\n\n'
        f'When you have made your choice click NEXT. [choose-card {cc_token(accepted or [card])}] [NEXT]\n\n'
        '[show NESW]\n\n'
        f'{prose}}}\n'
        '[BidSystemEW "2/1GF - 2/1 Game Force"]\n[BidSystemNS "2/1GF - 2/1 Game Force"]\n'
    )


def is_suit_raise(r, strains):
    """opp opened a suit in `strains` and raised it (1x-2x/3x/.., we silent); contract = that suit."""
    if r['context'] != 'opp_suit' or r['strain'] != 'suit':
        return False
    con = r['Contract']
    suit = con[1]
    if suit not in strains or int(con[0]) < 2:
        return False
    nz = [b for s, b in auction_calls(r) if b != 'PASS']
    return bool(nz) and all(re.match(r'^[1-7]' + suit + '$', b) for b in nz) and nz[0][0] == '1'


def is_major_raise(r):
    return is_suit_raise(r, 'HS')


def is_minor_raise(r):
    return is_suit_raise(r, 'CD')


def load_prose(event):
    """Per-deck bespoke-prose sidecar: coaching-curated/prose/<event>.json, mapping each
    board's OriginalSource key ('<scn> board <N>') to hand-authored prose. Missing -> {},
    so boards without an entry fall back to the template. Survives regeneration."""
    p = os.path.join('coaching-curated', 'prose', f'{event}.json')
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {}


# Board-order difficulty bands: clearest textbook leads open the deck, judgment close-calls
# land last; the seeded-random order is preserved WITHIN each band (so types stay mixed).
_LHO_DIFFICULTY = {'sequence': 0, 'AK': 0,
                   'interior_sequence': 1, 'singleton': 1, 'partners_suit': 1,
                   'judgment': 2}


def _compose_and_emit(boards, event, out_path, mix, blind_filter=False):
    """Classify (canon A), pick per `mix` (clear tiers mechanical, judgment via SD), emit.
    With blind_filter, judgment boards whose SD-chosen lead is not blind-defensible are
    skipped and replaced by later candidates (see judgment_blind_ok)."""
    import sd_lead
    by = {}
    for r in boards:
        tier, suit, card, _why = classify_suit_lead(hand_suits(r['south']), r['Contract'][1], r)
        r['_lead'] = (tier, suit, card)
        by.setdefault(tier, []).append(r)
    picked = []
    for tier, cnt in mix.items():
        if tier == 'judgment':
            continue
        picked.append(by.get(tier, [])[:cnt])
    jcap = mix.get('judgment', 0)
    jcands = by.get('judgment', []) if blind_filter else by.get('judgment', [])[:jcap]
    jlist = []
    for r in jcands:                                # judgment: SD picks the SUIT, convention the CARD
        if len(jlist) >= jcap:
            break
        suits = hand_suits(r['south']); trump = r['Contract'][1]
        cand = {s: card_code(s, conventional_lead_card(suits[s]))
                for s in SUITS if s != trump and conventional_lead_card(suits[s]) is not None}
        sc, _used = sd_lead.sd_scores(r['south'], r['Contract'], K=60)
        if not sc or not cand:
            continue
        best = max(cand, key=lambda s: sc.get(cand[s], (0, 0, 0))[2])  # best SUIT by SD...
        if blind_filter and not judgment_blind_ok(suits, trump, best, cand[best]):
            continue                                # 'DD chose blind' -> drop, take a later board
        r['_lead'] = ('judgment', best, cand[best])                    # ...conventional CARD in it
        jlist.append(r)
    picked.append(jlist)
    chosen = mixed_order(picked)                                 # seeded-random within each band
    chosen = sorted(chosen, key=lambda r: _LHO_DIFFICULTY.get(r['_lead'][0], 1))  # textbook first, fade to judgment
    bespoke = load_prose(event)                                  # hand-authored prose survives regeneration
    seen, blocks = {}, []
    for i, r in enumerate(chosen, start=1):
        tier, suit, card = r['_lead']
        accepted = widen_suit(hand_suits(r['south']), card, r, r['Contract'][1])
        key = f"{r['scn']} board {r['OriginalBoard']}"           # stable per-board key (== OriginalSource)
        prose = bespoke.get(key) or gen_prose_suit(tier, suit or card[0], card, seen.get(tier, 0))
        seen[tier] = seen.get(tier, 0) + 1
        blocks.append(emit_board(i, event, r, card, prose, accepted))
    with open(out_path, 'w') as f:
        f.write('\n'.join(blocks))
    return len(blocks), {t: len(v) for t, v in by.items()}


def build_major_deck(out_path):
    pool = [r for r in load_pool(natural_only=True, dedup=True) if is_major_raise(r)]
    return _compose_and_emit(pool, 'Basic_Major_Defense_LHO', out_path,
                             {'sequence': 9, 'interior_sequence': 3, 'singleton': 5, 'AK': 5, 'judgment': 8})


def build_minor_deck(out_path):
    pool = [r for r in load_pool(natural_only=True, dedup=True) if is_minor_raise(r)]
    # Mostly clear textbook leads; only 4 blind-defensible judgment close-calls (DD-filtered).
    return _compose_and_emit(pool, 'Basic_Minor_Defense_LHO', out_path,
                             {'sequence': 12, 'interior_sequence': 6, 'singleton': 2, 'AK': 6, 'judgment': 4},
                             blind_filter=True)


def build_competitive_deck(out_path):
    pool = [r for r in load_pool(natural_only=True, dedup=True)
            if r['context'] == 'competitive' and r['strain'] == 'suit']
    # Partner's-suit leads dominate (clear); only 3 blind-defensible judgment close-calls.
    return _compose_and_emit(pool, 'Competitive_Defense_LHO', out_path,
                             {'partners_suit': 13, 'sequence': 6, 'interior_sequence': 3, 'AK': 3, 'singleton': 2, 'judgment': 3},
                             blind_filter=True)


# ---------- third-hand (RHO) play deck ----------

PROSE_THIRD = {
    'third_hand_high': [
        "Play the {C} — third hand high. Partner led low and dummy followed low, so it is up to you: contribute your honour to win the trick or drive out declarer's, rather than let him score a cheap one.",
        "Play the {C}, third hand high. With dummy low, the third defender plays the high card — win the trick if you can, and at worst force a higher honour from declarer.",
    ],
    'third_low_of_touching': [
        "Play the {C}. Third hand plays high — but from a solid run you play the CHEAPEST: it wins just as well, and it tells partner you hold the touching cards above it.",
        "Play the {C}, the cheapest of your solid run. Equal cards win equally, so play the lowest and let partner read that you hold the honours above.",
    ],
}


def gen_prose_third(tier, card, variant):
    t = PROSE_THIRD[tier]
    return t[variant % len(t)].format(C=card_escape(card))


def classify_third_hand(led_suit, dummy_suits, south_suits):
    """South plays third after partner leads LOW in led_suit and dummy follows low.
    Canon C: third hand high; with touching honours play the lower. Returns
    (tier, card_code, why) or None (no clean decision / defer)."""
    d, s = dummy_suits[led_suit], south_suits[led_suit]
    if len(s) < 2:
        return None                              # singleton/void: no real choice
    if d and d[0] >= 11:
        return None                              # dummy has an honour -> cover/finesse case, defer
    if s[0] < 11:
        return None                              # no honour to contribute -> no clear lesson
    if s[0] - s[1] == 1:                          # solid run -> play the CHEAPEST of it
        i = 0                                     # descend while consecutive (KQJ->J, J109->9, AKQ->Q)
        while i + 1 < len(s) and s[i] - s[i + 1] == 1:
            i += 1
        return ('third_low_of_touching', card_code(led_suit, s[i]), 'cheapest of the solid run')
    if s[1] >= 11 and s[0] - s[1] >= 2:          # tenace (AQ/AJ/KJ) -> finesse judgement, drop
        return None
    return ('third_hand_high', card_code(led_suit, s[0]), 'third hand high')


def emit_third_board(n, event, r, led_card, card, prose):
    con = r['Contract']
    return (
        f'[Event "{event}"]\n[Site ""]\n[Board "{n}"]\n'
        f'[North "EPBot"]\n[East "EPBot"]\n[South "EPBot"]\n[West "EPBot"]\n'
        f'[Dealer "{r["Dealer"]}"]\n[Vulnerable "{r["Vulnerable"]}"]\n'
        f'[Deal "{r["Deal"]}"]\n[Scoring "MP"]\n[Declarer "W"]\n'
        f'[Contract "{con}"]\n[Result "{r.get("Result","")}"]\n[Student "S"]\n'
        f'[Category "Defense"]\n[Difficulty "beginner"]\n[SkillPath "defense/third_hand_play"]\n'
        f'[OriginalSource "{r["scn"]} board {r["OriginalBoard"]}, rotated so South is third hand"]\n'
        f'[Auction "{r["AuctionSeat"]}"]\n{fmt_auction(r["auction"])}\n'
        '{[show SE]\n'
        f'[showcards N:{led_card}]\n\n'
        f'Partner led the {card_escape(led_card)} and dummy plays low. You are third hand — which card do you play?\n\n'
        f'When you have chosen, click NEXT. [choose-card {card}] [NEXT]\n\n'
        '[show NESW]\n\n'
        f'{prose}}}\n'
        '[BidSystemEW "2/1GF - 2/1 Game Force"]\n[BidSystemNS "2/1GF - 2/1 Game Force"]\n'
    )


def build_third_hand_deck(out_path, event='Basic_NT_Defense_RHO', predicate=None):
    """Third-hand (RHO) deck for any context. predicate(r) selects boards; partner
    leads LOW in a SIDE suit, dummy low (no ruff), South plays third per canon C."""
    predicate = predicate or (lambda r: r['strain'] == 'NT')
    pool = load_pool(natural_only=True, dedup=True, target='W')   # declarer West -> South is third hand
    by = {}
    for r in pool:
        if not predicate(r):
            continue
        con = r['Contract']
        trump = con[1] if con[1] != 'N' else None
        dd = r['deal_dict']
        es = hand_suits(dd['E'])
        nlead = classify_lead(hand_suits(dd['N']))                # partner's principled (low) lead
        if not nlead or nlead[0] != 'fourth_best':                # need partner to lead LOW
            continue
        led_suit, led_card = nlead[1], nlead[2]
        if trump and (led_suit == trump or len(es[led_suit]) < 2):  # side suit + dummy can't ruff
            continue
        th = classify_third_hand(led_suit, es, hand_suits(dd['S']))
        if not th:
            continue
        tier, card, _why = th
        r['_th'] = (tier, led_card, card)
        by.setdefault(tier, []).append(r)
    chosen = mixed_order([by.get(t, [])[:n] for t, n in
                          {'third_hand_high': 22, 'third_low_of_touching': 8}.items()])[:30]
    chosen = sorted(chosen, key=lambda r: 0 if r['_th'][0] == 'third_hand_high' else 1)  # easy play first, touching last
    bespoke = load_prose(event)                                  # hand-authored prose survives regeneration
    seen, blocks = {}, []
    for i, r in enumerate(chosen[:30], start=1):
        tier, led_card, card = r['_th']
        v = seen.get(tier, 0); seen[tier] = v + 1
        key = f"{r['scn']} board {r['OriginalBoard']}"           # stable per-board key (== OriginalSource)
        prose = bespoke.get(key) or gen_prose_third(tier, card, v)
        blocks.append(emit_third_board(i, event, r, led_card, card, prose))
    with open(out_path, 'w') as f:
        f.write('\n'.join(blocks))
    return len(blocks), {t: len(v) for t, v in by.items()}


def build_third_major(out_path):
    return build_third_hand_deck(out_path, 'Basic_Major_Defense_RHO', is_major_raise)


def build_third_minor(out_path):
    return build_third_hand_deck(out_path, 'Basic_Minor_Defense_RHO', is_minor_raise)


def build_third_competitive(out_path):
    return build_third_hand_deck(out_path, 'Competitive_Defense_RHO',
                                 lambda r: r['context'] == 'competitive' and r['strain'] == 'suit')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--context', help='filter to one context for the examples')
    ap.add_argument('--examples', type=int, default=0)
    ap.add_argument('--leads', metavar='CONTEXT', help='classify SUIT leads (canon A) for a context')
    ap.add_argument('--build-major', metavar='OUT.pbn', help='generate the Basic_Major_Defense_LHO deck')
    ap.add_argument('--build-competitive', metavar='OUT.pbn', help='generate the Competitive_Defense_LHO deck')
    ap.add_argument('--build-minor', metavar='OUT.pbn', help='generate the Basic_Minor_Defense_LHO deck')
    ap.add_argument('--build-third', metavar='OUT.pbn', help='generate the Basic_NT_Defense_RHO (third-hand) deck')
    args = ap.parse_args()

    if args.build_major:
        n, avail = build_major_deck(args.build_major)
        print(f'wrote {n} boards to {args.build_major}')
        print(f'  available by tier: {avail}')
        return

    if args.build_competitive:
        n, avail = build_competitive_deck(args.build_competitive)
        print(f'wrote {n} boards to {args.build_competitive}')
        print(f'  available by tier: {avail}')
        return

    if args.build_minor:
        n, avail = build_minor_deck(args.build_minor)
        print(f'wrote {n} boards to {args.build_minor}')
        print(f'  available by tier: {avail}')
        return

    if args.build_third:
        n, avail = build_third_hand_deck(args.build_third)
        print(f'wrote {n} boards to {args.build_third}')
        print(f'  available by tier: {avail}')
        return

    if args.leads:
        nat = load_pool(natural_only=True, dedup=True)
        sub = [r for r in nat if r['context'] == args.leads and r['strain'] == 'suit']
        tiers = Counter()
        samples = {}
        for r in sub:
            trump = r['Contract'][1]
            t, suit, card, why = classify_suit_lead(hand_suits(r['south']), trump, r)
            tiers[t] += 1
            samples.setdefault(t, []).append((r, suit, card, why))
        print(f'context={args.leads} suit boards: {len(sub)}')
        print(f'  lead tiers (canon A): {dict(tiers)}')
        for t in ('partners_suit', 'sequence', 'singleton', 'AK', 'judgment'):
            for r, suit, card, why in samples.get(t, [])[:3]:
                print(f"   [{t:<13}] {r['Contract']:<4} lead {str(card):>3}  ({why})   S: {pretty(r['south'])}")
        return

    raw = load_pool(natural_only=False, dedup=False)
    nat = load_pool(natural_only=True, dedup=True)
    print(f'corpus boards (rotated, South on lead): {len(raw)}')
    print(f'NATURAL + deduped pool:                 {len(nat)}')
    print(f'  by context: {dict(Counter(r["context"] for r in nat))}')
    print(f'  by strain:  {dict(Counter(r["strain"] for r in nat))}')

    # partner-suit detection rate on auction-read contexts
    for ctx in ('competitive', 'we_opened'):
        sub = [r for r in nat if r['context'] == ctx]
        det = [r for r in sub if partner_real_suit(r)]
        print(f'  {ctx}: {len(sub)} boards, partner real suit detected on {len(det)} '
              f'({100*len(det)//max(len(sub),1)}%)')

    if args.examples:
        ctx = args.context or 'competitive'
        sub = [r for r in nat if r['context'] == ctx and partner_real_suit(r)]
        print(f'\n--- {ctx} examples (partner has a real suit) ---')
        for r in sub[:args.examples]:
            suit, kind, pos = partner_real_suit(r)
            suits = hand_suits(r['south'])
            card = partner_lead_card(suits, suit)
            print(f"  {r['scn']:<18} {r['Contract']:<4} partner {suit}({kind},{pos}) "
                  f"lead {str(card):>3}   S: {pretty(r['south'])}")


if __name__ == '__main__':
    main()
