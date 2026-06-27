#!/usr/bin/env python3
"""Select + rotate beginner opening-lead boards for a defense deck.

Reads a bba/<scn>.pbn pool (e.g. Basic_NT), keeps boards with a natural NT
auction declared by N/S, rotates each 90 degrees so the declarer sits East and
SOUTH is on lead (LHO), then classifies South's opening lead by PRINCIPLE
(leader's hand + auction), not by the double-dummy result. Prints ranked
candidates; with --emit writes a starter coaching-curated PBN (prose stubbed).

Run from project root:  python3 -P py/defense_lead_select.py bba/Basic_NT.pbn
"""
import re
import sys
import random
import argparse

SEATS = ['N', 'E', 'S', 'W']            # clockwise
IDX = {s: i for i, s in enumerate(SEATS)}
RANKVAL = {r: v for v, r in enumerate('23456789TJQKA', start=2)}
SUITS = ['S', 'H', 'D', 'C']            # spades hearts diamonds clubs (deal order)
SUITSYM = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}


# ---------- PBN parsing ----------

def parse_boards(path):
    boards = []
    cur = None
    in_auction = False
    with open(path) as f:
        for line in f:
            line = line.rstrip('\n')
            m = re.match(r'\[(\w+)\s+"([^"]*)"\]', line)
            if m:
                tag, val = m.group(1), m.group(2)
                if tag == 'Board':
                    if cur:
                        boards.append(cur)
                    cur = {'auction': []}
                    in_auction = False
                    cur['Board'] = val
                elif cur is not None:
                    cur[tag] = val
                    in_auction = (tag == 'Auction')
                continue
            if cur is not None and in_auction:
                t = line.strip()
                if t and not t.startswith('[') and not t.startswith('{') and not t.startswith('%'):
                    cur['auction'].extend(tok for tok in t.split() if tok)
    if cur:
        boards.append(cur)
    return boards


def deal_to_dict(dealstr):
    """'N:h h h h' -> {seat: 'spades.hearts.diamonds.clubs'} clockwise from prefix."""
    prefix, rest = dealstr.split(':', 1)
    hands = rest.split()
    start = IDX[prefix]
    return {SEATS[(start + i) % 4]: hands[i] for i in range(4)}


def dict_to_deal(d):
    return 'N:' + ' '.join(d[s] for s in SEATS)


# ---------- rotation (declarer -> East, South on lead) ----------

def rotate_to_east(board):
    """Return a rotated copy with Declarer=E and South the opening leader."""
    dec = board['Declarer']
    k = (IDX['E'] - IDX[dec]) % 4          # clockwise steps to move declarer onto E
    old = deal_to_dict(board['Deal'])
    new = {SEATS[t]: old[SEATS[(t - k) % 4]] for t in range(4)}

    def rseat(s):
        return SEATS[(IDX[s] + k) % 4]

    vul = board.get('Vulnerable', 'None')
    if k % 2 == 1:                          # 90/270 swaps the NS<->EW axis
        vul = {'NS': 'EW', 'EW': 'NS'}.get(vul, vul)

    return {
        'Deal': dict_to_deal(new),
        'Dealer': rseat(board.get('Dealer', 'N')),
        'Declarer': 'E',
        'Vulnerable': vul,
        'AuctionSeat': rseat(board.get('Auction', board.get('Dealer', 'N'))),
        'Contract': board['Contract'],
        'Result': board.get('Result', ''),
        'auction': board['auction'],
        'south': new['S'],
        'OriginalBoard': board['Board'],
    }


# ---------- hand helpers ----------

def hand_suits(handstr):
    """'spades.hearts.diamonds.clubs' -> {suit: [rankvals desc]}."""
    parts = handstr.split('.')
    out = {}
    for suit, cards in zip(SUITS, parts):
        out[suit] = sorted((RANKVAL[c] for c in cards), reverse=True)
    return out


def hcp(suits):
    return sum(max(0, v - 10) for s in suits for v in suits[s])


def pretty(handstr):
    parts = handstr.split('.')
    return '  '.join(f'{SUITSYM[s]}{c or "-"}' for s, c in zip(SUITS, parts))


def card_code(suit, val):
    rank = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T'}.get(val, str(val))
    return f'{suit}{rank}'


# ---------- opening-lead classifier (principle-based, vs NT) ----------

def classify_lead(suits):
    """Return (tier, suit, card_code, reason) for the textbook NT lead, or None.

    Tiers (best -> worst): sequence, broken_sequence, fourth_best.
    Attack the LONGEST suit; drop ambiguous / no-honor / freak hands.
    """
    lengths = {s: len(suits[s]) for s in SUITS}
    maxlen = max(lengths.values())
    if maxlen < 4:
        return None                          # no long suit to attack vs NT
    longest = [s for s in SUITS if lengths[s] == maxlen]

    def seq_info(cards):
        """cards: rankvals desc. -> 'solid' | 'broken' | None for a 3-card top run.

        Top must be J/Q/K (11..13): ace-headed runs (AKQ, AKJ) invoke the
        'lead the K from AK' wrinkle and are not clean beginner top-of-sequence
        teaches, so they are excluded.
        """
        if len(cards) < 3:
            return None
        a, b, c = cards[0], cards[1], cards[2]
        if not (11 <= a <= 13):              # top honor, but not the ace
            return None
        if a - b == 1 and b - c == 1:
            return 'solid'                   # KQJ, QJT, JT9
        if a - b == 1 and b - c == 2:
            return 'broken'                  # KQT, QJ9, JT8
        return None

    # Prefer a longest suit that carries a sequence.
    seq_suits = [(s, seq_info(suits[s])) for s in longest]
    seq_suits = [(s, kind) for s, kind in seq_suits if kind]
    if seq_suits:
        if len({s for s, _ in seq_suits}) > 1:
            return None                      # two equally-long sequence suits = ambiguous
        s, kind = seq_suits[0]
        top = suits[s][0]
        tier = 'sequence' if kind == 'solid' else 'broken_sequence'
        return (tier, s, card_code(s, top), f'top of a {kind} sequence in your long suit')

    # No sequence in the longest suit. Need a single, unambiguous longest suit.
    if len(longest) != 1:
        return None
    s = longest[0]
    cards = suits[s]

    if cards[0] == 14 and cards[1] == 13:     # A-K on top: lead an honour (special) -> drop
        return None

    # Interior sequence: a higher honour, a gap, then a touching run just below it
    # (AJT->J, KJT->J, AQJ->Q, QT9->T). Lead the top of the inner run.
    for i in range(1, len(cards) - 1):
        if cards[i] - cards[i + 1] == 1 and cards[i] >= 10 and cards[i - 1] - cards[i] >= 2:
            return ('interior_sequence', s, card_code(s, cards[i]),
                    'top of an interior sequence in your long suit')

    if cards[0] >= 11:                        # an honour, no sequence -> fourth best
        return ('fourth_best', s, card_code(s, cards[3]),
                'fourth highest from your long, broken suit')

    # No honour in the long suit -> top of nothing (lead high to deny an honour).
    return ('top_of_nothing', s, card_code(s, cards[0]),
            'top of nothing in your long suit')


def conventional_lead_card(cards):
    """The conventional opening-lead card VALUE from ONE suit's holding (rankvals desc),
    or None if void. Signal-correct: top of a 3-card/interior sequence; 4th-best from a
    4+ suit with an honour; top-of-nothing (the TOP card) from a no-honour suit; top of a
    doubleton; low from a 3-card honour holding. Used to pick the CARD on judgement boards
    once SD has chosen the suit — so the spot-card never lies to partner."""
    n = len(cards)
    if n == 0:
        return None
    if n >= 3 and 11 <= cards[0] <= 13 and cards[0] - cards[1] == 1 and cards[1] - cards[2] in (1, 2):
        return cards[0]                          # top of a 3-card sequence
    for i in range(1, n - 1):                     # interior sequence (KJT, AJT, QT9...)
        if cards[i] - cards[i + 1] == 1 and cards[i] >= 10 and cards[i - 1] - cards[i] >= 2:
            return cards[i]
    if cards[0] >= 11 and n >= 4:
        return cards[3]                          # 4th best from an honour suit
    if cards[0] < 11:
        return cards[0]                          # no honour -> top of nothing (lead the top)
    if n == 2:
        return cards[0]                          # honour doubleton -> top
    return cards[-1]                             # honour, 3 cards -> low from an honour


NATURAL_NT = {'1N', '1NT', '2N', '2NT', '3N', '3NT', 'PASS', 'P'}
TIER_RANK = {'sequence': 0, 'broken_sequence': 1, 'interior_sequence': 2,
             'fourth_best': 3, 'top_of_nothing': 4}


def natural_auction(auction):
    return all(re.sub(r'[!?]', '', t).upper() in NATURAL_NT for t in auction)


def candidates(boards):
    out = []
    for b in boards:
        if b.get('Declarer') not in ('N', 'S'):
            continue
        if b.get('Contract', '') not in ('1N', '2N', '3N'):
            continue
        if not natural_auction(b['auction']):
            continue
        r = rotate_to_east(b)
        suits = hand_suits(r['south'])
        lens = [len(suits[s]) for s in SUITS]
        if min(lens) == 0 or max(lens) >= 7:  # drop voids / freak shapes for beginners
            continue
        h = hcp(suits)
        if h > 12:                           # beginner defender
            continue
        lead = classify_lead(suits)
        if not lead:
            continue
        tier, suit, card, reason = lead
        r.update(tier=tier, lead_suit=suit, lead_card=card, reason=reason, hcp=h,
                 maxlen=max(len(suits[s]) for s in SUITS))
        out.append(r)
    out.sort(key=lambda r: (TIER_RANK[r['tier']], -r['maxlen'], r['Contract']))
    return out


# ---------- deck emission (coaching-curated PBN) ----------

SUITWORD = {'S': 'spade', 'H': 'heart', 'D': 'diamond', 'C': 'club'}
CONWORDS = {'1N': '1NT', '2N': '2NT', '3N': '3NT'}

PROSE = {
    'sequence': [
        "Lead the {C}, the top of your \\{X} sequence. Three touching honours make the top card completely safe — it can never cost a trick, and it tells partner you hold the ones just beneath it. Against notrump you attack your longest, strongest suit to drive out declarer's stoppers and build winners, and \\{X} is plainly that suit.",
        "Lead the {C}. With a solid three-card sequence you lead the top honour: the standard, no-risk card that also promises the cards below it. Notrump defence is a race to set up tricks in your long suit before declarer cashes his, so attack \\{X} from the top.",
        "Lead the {C}, top of your \\{X} sequence. A run of honours is a defender's friend — lead the highest, knock out declarer's guard, and your long suit is on its way to becoming tricks.",
    ],
    'broken_sequence': [
        "Lead the {C}, the top of your \\{X} sequence. It is only a broken sequence, but with two touching honours and another close behind you treat it the same way — lead the top honour, safe and clear, to develop your long suit against notrump.",
        "Lead the {C}. Your \\{X} holding is almost solid, and a near-sequence is led like a real one: top honour first, knocking out declarer's stopper while you build your suit.",
        "Lead the {C}, top of your broken \\{X} sequence. Two honours in a row with a third close by play just like a solid run — lead the highest and go to work on your long suit.",
    ],
    'interior_sequence': [
        "Lead the {C}, the top of your interior sequence in \\{X}. You hold a higher honour, a gap, then a touching run just below — lead the top of that run: it drives out a stopper while your high card stays poised above declarer. Against notrump, attack your long suit.",
        "Lead the {C}. With a high honour and a touching pair beneath it, lead the top of the inner run — it develops your long \\{X} suit without throwing your top card under the bus.",
    ],
    'fourth_best': [
        "Lead the {C}, fourth highest from your long \\{X} suit. With honours but no sequence to lead from, fourth-best is the classic notrump attack — you invest a little to develop your longest suit, hoping partner holds a card that helps it come in.",
        "Lead the {C}, fourth down in \\{X}. There is no sequence here, so you fall back on the bread-and-butter notrump lead: fourth highest of your longest, strongest suit, aiming to set up tricks before declarer can run his.",
        "Lead the {C}, fourth best in your long \\{X} suit. No three-in-a-row to lead from, so lead low — fourth from the top — and try to build length tricks in the suit where you are longest.",
    ],
    'top_of_nothing': [
        "Lead the {C}, top of nothing. Your long \\{X} suit holds no honour, so lead the highest spot — a low card would promise an honour and mislead partner. Vs notrump you still attack your longest suit and hope partner supplies the high cards.",
        "Lead the {C}, the top of a worthless \\{X} suit. Leading high denies an honour and keeps partner honest; your length is the asset — develop it and let partner's honours do the work.",
    ],
}

# Hand-polished prose for the pilot board (Basic_NT #13), kept verbatim.
PILOT_PROSE = (
    "Lead the \\SQ, the top of your three-card sequence. With Q-J-T you can lead the top "
    "honor in complete safety — it can never cost a trick and it tells partner you hold the "
    "cards just beneath it.\n\nAgainst notrump you attack your longest, strongest suit to drive "
    "out declarer's stoppers and set up winners before he can run his own. Here that suit is "
    "plainly your spades, so the only question is which spade, and top of the solid sequence is "
    "the textbook answer.\n\nKeep leading spades each time you regain the lead. The right lead is "
    "still the right lead even when declarer has the values to bring it home: you make him work "
    "for every trick and you are ready to cash your suit the moment partner finds an entry."
)


def card_escape(code):
    """'SQ' -> '\\SQ' ; 'DT' -> '\\D10' (ten shows as 10 to match the hand display)."""
    suit, rank = code[0], code[1:]
    if rank == 'T':
        rank = '10'
    return '\\' + suit + rank


def format_auction(bids):
    lines = []
    for i in range(0, len(bids), 4):
        row = bids[i:i + 4]
        lines.append('  '.join(f'{b:<5}' for b in row).rstrip())
    return '\n'.join(lines)


def gen_prose(tier, suit, code, variant):
    return PROSE[tier][variant % len(PROSE[tier])].format(C=card_escape(code), X=suit)


def cc_token(cards):
    """Render a [choose-card ...] argument: a single code, or 'any:a,b' (principled
    first) when the board is widened to accept a reasonable alternative SUIT."""
    seen = list(dict.fromkeys(c for c in cards if c))
    return seen[0] if len(seen) <= 1 else 'any:' + ','.join(seen)


def widen_nt(suits, principled):
    """TIGHT widening (vs NT): accept the principled card, plus a second card ONLY when
    another suit is independently a STRONG standard lead (a solid/broken/interior
    SEQUENCE). Found by re-running the classifier on the hand minus the principled suit.
    A 4th-best/top-of-nothing second is NOT coequal, so it does not widen — and never a
    different card of the SAME suit (the equal-honour signal rule)."""
    psuit = principled[0]
    reduced = {s: (suits[s] if s != psuit else []) for s in SUITS}
    second = classify_lead(reduced)
    if second and second[0] in ('sequence', 'broken_sequence', 'interior_sequence'):
        return [principled, second[2]]
    return [principled]


def emit_board(n, c, prose):
    con = c['Contract']
    bids = format_auction(['Pass' if b.upper() in ('P', 'PASS') else b for b in c['auction']])
    return (
        f'[Event "Basic_NT_Defense_LHO"]\n[Site ""]\n[Board "{n}"]\n'
        f'[North "EPBot"]\n[East "EPBot"]\n[South "EPBot"]\n[West "EPBot"]\n'
        f'[Dealer "{c["Dealer"]}"]\n[Vulnerable "{c["Vulnerable"]}"]\n'
        f'[Deal "{c["Deal"]}"]\n[Scoring "MP"]\n[Declarer "E"]\n'
        f'[Contract "{con}"]\n[Result "{c["Result"]}"]\n[Student "S"]\n'
        f'[Category "Defense"]\n[Difficulty "beginner"]\n[SkillPath "defense/opening_leads"]\n'
        f'[OriginalSource "Basic_NT board {c["OriginalBoard"]}, rotated 90 so South is on lead"]\n'
        f'[Auction "{c["AuctionSeat"]}"]\n{bids}\n'
        '{[show S]\n\n'
        f'The opponents have bid to {CONWORDS[con]} and it is your lead.\n\n'
        f'When you have made your choice click NEXT. [choose-card {cc_token(c.get("accepted") or [c["lead_card"]])}] [NEXT]\n\n'
        '[show NESW]\n\n'
        f'{prose}}}\n'
        '[BidSystemEW "2/1GF - 2/1 Game Force"]\n[BidSystemNS "2/1GF - 2/1 Game Force"]\n'
    )


def _blend_by_contract(cands, n):
    """Round-robin 3N -> 2N -> 1N for contract variety (game-leaning)."""
    buckets = {'3N': [], '2N': [], '1N': []}
    for c in cands:
        buckets[c['Contract']].append(c)
    out, order = [], ['3N', '2N', '1N']
    while len(out) < n and any(buckets.values()):
        for con in order:
            if buckets[con]:
                out.append(buckets[con].pop(0))
                if len(out) >= n:
                    break
    return out


# Target 30-board mix across all five lead types (variety over honor-sequence glut).
DECK_MIX = {'sequence': 6, 'broken_sequence': 5, 'interior_sequence': 5,
            'fourth_best': 8, 'top_of_nothing': 6}


_ORDER_SEED = 17


def mixed_order(buckets, seed=_ORDER_SEED):
    """Flatten the per-tier buckets and SEEDED-shuffle, so board order is random —
    not clustered, and not a predictable rotation. Deterministic (reproducible)."""
    flat = [x for b in buckets for x in b]
    random.Random(seed).shuffle(flat)
    return flat


def select_deck(cands, mix=None):
    """Balanced 30 across all lead types, contract-blended, then SEEDED-RANDOM order
    so the lead kinds are neither clustered nor predictably rotated."""
    mix = mix or DECK_MIX
    by = {t: [] for t in TIER_RANK}
    for c in cands:
        by[c['tier']].append(c)
    picked = []
    for tier in TIER_RANK:
        n = mix.get(tier, 0)
        pool = by[tier]
        if tier == 'sequence':
            pilot = next((c for c in pool if c['OriginalBoard'] == '13'), None)
            if pilot:
                picked.append([pilot] + _blend_by_contract([c for c in pool if c is not pilot], n - 1))
                continue
        picked.append(_blend_by_contract(pool, n))
    return mixed_order(picked)                    # seeded-random, not clustered, not rotated


def emit_deck(cands, out_path):
    deck = select_deck(cands)
    # per-tier variant counter for prose variety
    from collections import defaultdict
    seen = defaultdict(int)
    blocks = []
    for i, c in enumerate(deck, start=1):
        c['accepted'] = widen_nt(hand_suits(c['south']), c['lead_card'])
        if c['OriginalBoard'] == '13':
            prose = PILOT_PROSE
        else:
            prose = gen_prose(c['tier'], c['lead_suit'], c['lead_card'], seen[c['tier']])
        seen[c['tier']] += 1
        blocks.append(emit_board(i, c, prose))
    with open(out_path, 'w') as f:
        f.write('\n'.join(blocks))
    return len(deck)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pool', help='path to bba/<scn>.pbn')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--emit', metavar='OUT.pbn', help='write a 30-board coaching-curated deck')
    args = ap.parse_args()

    boards = parse_boards(args.pool)
    cands = candidates(boards)

    if args.emit:
        n = emit_deck(cands, args.emit)
        print(f'wrote {n} boards to {args.emit}')
        return

    from collections import Counter
    by_tier = Counter(c['tier'] for c in cands)
    by_con = Counter(c['Contract'] for c in cands)
    print(f'pool boards: {len(boards)}   candidates: {len(cands)}')
    print(f'  by tier: {dict(by_tier)}')
    print(f'  by contract: {dict(by_con)}')
    print('-' * 100)
    show = cands[:args.limit] if args.limit else cands
    for c in show:
        print(f"#{c['OriginalBoard']:>3} {c['Contract']} {c['Vulnerable']:>4} "
              f"lead {c['lead_card']:>3} [{c['tier']:<15}] hcp{c['hcp']:>2}  "
              f"S: {pretty(c['south'])}   ({c['reason']})")


if __name__ == '__main__':
    main()
