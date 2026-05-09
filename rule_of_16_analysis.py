#!/usr/bin/env python3
"""
Analyze Mel's Rule of 16: After 1NT(N, 15-17), with 8-9 HCP balanced and
R16 = HCP + (cards 8 or higher), South's choice:
  - R16 > 15: bid 3NT
  - R16 <= 15: Pass 1NT

Standard alternative: always invite with 2NT (opener with 15 declines, settles at 2NT).

Compares scoring of hypothesis vs three baselines (always Pass, always 2NT, always 3NT).
"""

import re
from pathlib import Path

DD_FILE = Path("/tmp/rule_of_16_dd.pbn")

# Card values for HCP and cards >= 8
HCP_VALUES = {'A': 4, 'K': 3, 'Q': 2, 'J': 1, 'T': 0, '9': 0, '8': 0,
              '7': 0, '6': 0, '5': 0, '4': 0, '3': 0, '2': 0}

def parse_hand(hand_str):
    """hand_str like 'Q54.AJT53.AQ.Q84' returns (HCP, cards_ge_8)."""
    suits = hand_str.split('.')
    hcp = 0
    ge_8 = 0
    for suit in suits:
        for c in suit:
            hcp += HCP_VALUES.get(c, 0)
            # Cards >= 8: A, K, Q, J, T, 9, 8
            if c in 'AKQJT98':
                ge_8 += 1
    return hcp, ge_8

def parse_boards(pbn_path):
    text = Path(pbn_path).read_text()
    boards = re.split(r'\n(?=\[Event)', text)
    parsed = []
    for b in boards:
        if '[Board' not in b:
            continue
        d = {}
        m = re.search(r'\[Board "(\d+)"\]', b)
        d['board'] = int(m.group(1))
        m = re.search(r'\[Vulnerable "(\w+)"\]', b)
        d['vul'] = m.group(1)
        m = re.search(r'\[Deal "([NESW]):([^"]+)"\]', b)
        if m:
            first_seat = m.group(1)
            hands = m.group(2).split()
            # Order in PBN: starts with first_seat, goes clockwise (N E S W)
            seats_order = ['N', 'E', 'S', 'W']
            start_idx = seats_order.index(first_seat)
            hand_by_seat = {}
            for i, h in enumerate(hands):
                hand_by_seat[seats_order[(start_idx + i) % 4]] = h
            d['hands'] = hand_by_seat
            s_hcp, s_ge_8 = parse_hand(hand_by_seat['S'])
            d['hcp_s'] = s_hcp
            d['r16_s'] = s_hcp + s_ge_8
            d['hcp_n'], _ = parse_hand(hand_by_seat['N'])
        m = re.search(r'\[OptimumResultTable "([^"]+)"\]', b)
        if m:
            tbl = m.group(1).replace('\\n', '\n')
            lines = tbl.strip().split('\n')
            dd = {}
            for line in lines[1:]:
                parts = line.split()
                seat = parts[0]
                dd[seat] = {'NT': int(parts[1]), 'S': int(parts[2]),
                            'H': int(parts[3]), 'D': int(parts[4]), 'C': int(parts[5])}
            d['dd'] = dd
        parsed.append(d)
    return parsed

def vul_for_seat(vul_str, seat):
    if vul_str == 'All':
        return True
    if vul_str == 'None':
        return False
    if vul_str == 'NS':
        return seat in ('N', 'S')
    if vul_str == 'EW':
        return seat in ('E', 'W')
    return False

def score_nt_by_n(level, dd, vul_str):
    """Score for level-NT contract by N, using DD."""
    tricks = dd['N']['NT']
    vul = vul_for_seat(vul_str, 'N')
    contract_tricks = level + 6
    if tricks >= contract_tricks:
        base = 40 + 30 * (level - 1)
        if base >= 100:
            game = 500 if vul else 300
        else:
            game = 50
        ot = 30 * (tricks - contract_tricks)
        slam = 0
        if level == 6:
            slam = 750 if vul else 500
        elif level == 7:
            slam = 1500 if vul else 1000
        return base + game + ot + slam
    else:
        ut = contract_tricks - tricks
        return -(100 if vul else 50) * ut

def imp(diff):
    table = [
        (20, 0), (40, 1), (80, 2), (120, 3), (160, 4), (210, 5),
        (260, 6), (310, 7), (360, 8), (420, 9), (490, 10), (590, 11),
        (740, 12), (890, 13), (1090, 14), (1290, 15), (1490, 16),
        (1740, 17), (1990, 18), (2240, 19), (2490, 20), (2990, 21),
    ]
    a = abs(diff)
    for limit, imps in table:
        if a <= limit:
            return imps if diff > 0 else -imps
    return 24 if diff > 0 else -24

def main():
    boards = parse_boards(DD_FILE)
    boards = [b for b in boards if 'dd' in b and 'r16_s' in b]
    print(f"Boards with DD and parsed hands: {len(boards)}")

    # R16 distribution
    r16_dist = {}
    for b in boards:
        r16_dist[b['r16_s']] = r16_dist.get(b['r16_s'], 0) + 1
    print("\nR16 distribution (S):")
    for k in sorted(r16_dist):
        print(f"  R16={k}: {r16_dist[k]}")

    # Compare strategies
    # Hypothesis: pass if R16<=15, 3NT if R16>15
    # Always 1NT: pass
    # Always 2NT: invite (opener declines with 15, settles 2NT)
    # Always 3NT: drive

    def hypo_score(b):
        if b['r16_s'] > 15:
            return score_nt_by_n(3, b['dd'], b['vul'])
        else:
            return score_nt_by_n(1, b['dd'], b['vul'])

    strategies = {
        'Hypothesis (R16 rule)': hypo_score,
        'Always Pass (1NT)': lambda b: score_nt_by_n(1, b['dd'], b['vul']),
        'Always 2NT (invite)': lambda b: score_nt_by_n(2, b['dd'], b['vul']),
        'Always 3NT': lambda b: score_nt_by_n(3, b['dd'], b['vul']),
    }
    avg_scores = {}
    for name, fn in strategies.items():
        avg = sum(fn(b) for b in boards) / len(boards)
        avg_scores[name] = avg
    print()
    print("=" * 70)
    print("Average score per deal (NS) by strategy:")
    print("=" * 70)
    for name, avg in sorted(avg_scores.items(), key=lambda x: -x[1]):
        print(f"  {name:<30} {avg:+.1f}")
    print()

    # Head-to-head: hypothesis vs each baseline
    print("=" * 70)
    print("Hypothesis (R16 rule) vs each baseline (per deal IMP comparison):")
    print("=" * 70)
    for name, fn in strategies.items():
        if name == 'Hypothesis (R16 rule)':
            continue
        h_wins = s_wins = pushes = 0
        net_imps = 0
        for b in boards:
            hypo = hypo_score(b)
            std = fn(b)
            imps = imp(hypo - std)
            net_imps += imps
            if imps > 0:
                h_wins += 1
            elif imps < 0:
                s_wins += 1
            else:
                pushes += 1
        print(f"\nvs {name}:")
        print(f"  H wins: {h_wins}  S wins: {s_wins}  Pushes: {pushes}")
        print(f"  Net IMPs (hypothesis): {net_imps:+d}")
        print(f"  Average IMPs/deal:      {net_imps/len(boards):+.2f}")

    # By R16 — show which decision (Pass/3NT) the rule recommends and how it does
    print()
    print("=" * 70)
    print("By R16 value: hypothesis decision and outcome")
    print("=" * 70)
    print(f"{'R16':<5} {'Count':<6} {'Action':<8} {'Avg DD tricks':<14} {'Avg Score':<10} {'vs 2NT IMPs':<12}")
    for r16 in sorted(r16_dist):
        sub = [b for b in boards if b['r16_s'] == r16]
        action = '3NT' if r16 > 15 else 'Pass'
        avg_t = sum(b['dd']['N']['NT'] for b in sub) / len(sub)
        avg_h = sum(hypo_score(b) for b in sub) / len(sub)
        avg_2nt = sum(score_nt_by_n(2, b['dd'], b['vul']) for b in sub) / len(sub)
        net_imps = sum(imp(hypo_score(b) - score_nt_by_n(2, b['dd'], b['vul'])) for b in sub)
        print(f"{r16:<5} {len(sub):<6} {action:<8} {avg_t:<14.2f} {avg_h:<+10.1f} {net_imps:+d}")

if __name__ == '__main__':
    main()
