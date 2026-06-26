#!/usr/bin/env python3
"""Single-dummy opening-lead scorer + three-tier grader.

For a board where South is on lead vs an NT contract, Monte-Carlo single-dummy:
hold South's 13 cards, deal the hidden 39 many times consistent with the auction
(declarer/partner point ranges), double-dummy-solve each layout, and average each
candidate lead's defensive tricks. The result is an objective 0-100 score per card.

Grading (David's model):
  correct (atta-boy) = the principled card in the top-score group
                       (top of sequence / fourth best, via classify_lead)
  reasonable         = any other lead within REASONABLE_MARGIN of the top score
  wrong              = everything else

Run from project root:  python3 -P py/sd_lead.py coaching-curated/Basic_NT_Defense_LHO.pbn --boards 1 2 11 19
"""
import os
import sys
import random
import argparse
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # end of path: don't shadow stdlib (select)
from defense_lead_select import (
    parse_boards, deal_to_dict, hand_suits, classify_lead, SUITS, SUITSYM,
)
from endplay.types import Deal, Player, Denom
from endplay.dds import solve_board

RANKS = '23456789TJQKA'
HCP = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
SYM2LET = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
REASONABLE_MARGIN = 15          # within 15 of top (0-100) counts as "reasonable"

DENOM = {'S': Denom.spades, 'H': Denom.hearts, 'D': Denom.diamonds,
         'C': Denom.clubs, 'N': Denom.nt}
# Combined declaring-side HCP band by contract LEVEL (game-leaning — the
# "less conservative bidders" default). Suit contracts also require an 8-card fit.
HCP_BAND = {1: (19, 23), 2: (20, 24), 3: (22, 26), 4: (24, 29),
            5: (25, 30), 6: (28, 33), 7: (31, 37)}


def hcp(ranks):
    return sum(HCP.get(r, 0) for r in ranks)


def sd_scores(south, contract, K=150, seed=7):
    """Trump-aware Monte-Carlo single-dummy. south: 'spades.hearts.diamonds.clubs';
    contract e.g. '4H' / '3N' (trailing X/XX ok). Returns {cardcode: (avg, set%, score)}.

    The hidden 39 are dealt so the declaring side (E+W) holds the level-appropriate
    combined HCP and — for a suit contract — an 8+ card trump fit. solve_board is run
    with the contract strain as trump.
    """
    rng = random.Random(seed)
    level = int(contract[0]); strain = contract[1]
    trump = DENOM[strain]
    lo, hi = HCP_BAND.get(level, (20, 30))
    fit_min = 0 if strain == 'N' else 8
    need = 13 - (6 + level) + 1                 # defensive tricks to set the contract

    parts = south.split('.')
    sc = [(s, r) for s, p in zip(SUITS, parts) for r in p]
    pool = [(s, r) for s in SUITS for r in RANKS if (s, r) not in sc]

    def make():
        for _ in range(1500):
            rng.shuffle(pool)
            E, W = pool[13:26], pool[26:]
            if not (lo <= hcp([r for _, r in E]) + hcp([r for _, r in W]) <= hi):
                continue
            if fit_min and sum(s == strain for s, _ in E) + sum(s == strain for s, _ in W) < fit_min:
                continue
            return {'N': pool[:13], 'E': E, 'S': sc, 'W': W}
        return None

    def pbn(d):
        def fmt(cs):
            by = {s: ''.join(sorted((r for ss, r in cs if ss == s),
                                    key=lambda x: -RANKS.index(x))) for s in SUITS}
            return '.'.join(by[s] for s in SUITS)
        return 'N:' + ' '.join(fmt(d[s]) for s in ('N', 'E', 'S', 'W'))

    tot, st, n = defaultdict(float), defaultdict(int), 0
    for _ in range(K):
        d = make()
        if not d:
            continue
        deal = Deal(pbn(d)); deal.trump = trump; deal.first = Player.south
        for card, tr in solve_board(deal):
            s = str(card); key = SYM2LET[s[0]] + s[1:]
            tot[key] += tr; st[key] += 1 if tr >= need else 0
        n += 1
    if not n:
        return {}, 0
    best = max(tot.values()) / n
    return ({k: (tot[k] / n, 100 * st[k] / n, 100 * (tot[k] / n) / best if best else 0)
             for k in tot}, n)


def grade(scores, principled):
    """Assign tiers. Returns {card: 'correct'|'reasonable'|'wrong'}.

    correct    = the principled card (atta-boy).
    reasonable = within REASONABLE_MARGIN of the top score, OR same suit as the
                 correct card (right suit, wrong card = right idea).
    wrong      = everything else.
    """
    if not scores:
        return {}
    top = max(v[2] for v in scores.values())
    correct_suit = principled[0] if principled else None
    tiers = {}
    for k, (_, _, score) in scores.items():
        if k == principled:
            tiers[k] = 'correct'
        elif score >= top - REASONABLE_MARGIN or (correct_suit and k[0] == correct_suit):
            tiers[k] = 'reasonable'
        else:
            tiers[k] = 'wrong'
    return tiers


def droppable(tiers):
    """A board is droppable if no lead grades 'wrong' — nothing to get wrong,
    so the exercise can't distinguish a good lead from a bad one."""
    return not any(t == 'wrong' for t in tiers.values())


def pretty_hand(suits):
    R = {14: "A", 13: "K", 12: "Q", 11: "J", 10: "T"}
    return '  '.join(f'{SUITSYM[s]}{"".join(R.get(v, str(v)) for v in suits[s]) or "-"}' for s in SUITS)


def score_one(south, con, K):
    suits = hand_suits(south)
    lead = classify_lead(suits)
    principled = lead[2] if lead else None
    scores, used = sd_scores(south, con, K=K)
    tiers = grade(scores, principled)
    return suits, principled, scores, tiers, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('deck', help='deck PBN, or bba/<scn>.pbn with --pool')
    ap.add_argument('--boards', nargs='*', type=int, default=[])
    ap.add_argument('--pool', action='store_true', help='score the full candidate pool (bba source)')
    ap.add_argument('-K', type=int, default=150)
    args = ap.parse_args()

    if args.pool:
        from defense_lead_select import candidates
        cands = candidates(parse_boards(args.deck))
        keep, drop, disagree = [], [], []
        for c in cands:
            suits, principled, scores, tiers, used = score_one(c['south'], c['Contract'], args.K)
            if not scores:
                continue
            top_card = max(scores, key=lambda k: scores[k][2])
            if principled and top_card[0] != principled[0]:
                disagree.append(c['OriginalBoard'])
            (drop if droppable(tiers) else keep).append(c['OriginalBoard'])
        print(f'pool candidates scored: {len(keep)+len(drop)}  (K={args.K})')
        print(f'  KEEP (gradable, has a wrong tier): {len(keep)}')
        print(f'  DROP (no wrong tier, lead irrelevant): {len(drop)}  e.g. {drop[:12]}')
        print(f'  principle-vs-SD suit disagreement (flag): {len(disagree)}  e.g. {disagree[:12]}')
        return

    boards = parse_boards(args.deck)
    want = set(args.boards) if args.boards else None
    for b in boards:
        n = int(b['Board'])
        if want and n not in want:
            continue
        suits, principled, scores, tiers, used = score_one(deal_to_dict(b['Deal'])['S'], b['Contract'], args.K)
        flag = '  <<< DROP (no wrong tier)' if droppable(tiers) else ''
        print(f'\nBoard {n}  {b["Contract"]}  (SD layouts={used})   S: {pretty_hand(suits)}{flag}')
        print(f'  correct (principled): {principled}')
        for k, (avg, setp, score) in sorted(scores.items(), key=lambda kv: -kv[1][2])[:8]:
            print(f'    {k:<4} score{score:4.0f}  set{setp:3.0f}%  [{tiers.get(k,"?")}]')


if __name__ == '__main__':
    main()
