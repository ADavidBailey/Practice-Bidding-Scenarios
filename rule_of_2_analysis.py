#!/usr/bin/env python3
"""
Analyze Mel's Rule of 2: After 1NT-Pass-Pass, balance with 2+ distribution points.

Compares scoring of:
  - Standard (Pass): 1NT by W defended by NS, DD trick counts.
  - Hypothesis (Balance): NS plays best partscore (max of 2-level contracts).

Uses /tmp/rule_of_2_dd.pbn (DD-analyzed) for fair scoring on both paths.
"""

import re
from pathlib import Path

DD_FILE = Path("/tmp/rule_of_2_dd.pbn")

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
        m = re.search(r'\{HCP (\d+) (\d+) (\d+) (\d+)\}', b)
        if m:
            d['hcp_n'], d['hcp_e'], d['hcp_s'], d['hcp_w'] = (int(x) for x in m.groups())
        m = re.search(r'\{Shape (\w+) (\w+) (\w+) (\w+)\}', b)
        if m:
            d['shape_n'], d['shape_e'], d['shape_s'], d['shape_w'] = m.groups()
        m = re.search(r'\[OptimumResultTable "([^"]+)"\]', b)
        if m:
            tbl = m.group(1).replace('\\n', '\n')
            lines = tbl.strip().split('\n')
            dd = {}
            for line in lines[1:]:
                parts = line.split()
                seat = parts[0]
                dd[seat] = {
                    'NT': int(parts[1]),
                    'S': int(parts[2]),
                    'H': int(parts[3]),
                    'D': int(parts[4]),
                    'C': int(parts[5]),
                }
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

def score_contract(level, strain, declarer, tricks_made, vul, doubled=0):
    """Returns NS score (positive if good for NS)."""
    contract_tricks = level + 6
    is_ns = declarer in ('N', 'S')
    sign = 1 if is_ns else -1
    declarer_vul = vul

    if tricks_made >= contract_tricks:
        if strain == 'NT':
            base = 40 + 30 * (level - 1)
        elif strain in ('H', 'S'):
            base = 30 * level
        else:
            base = 20 * level
        if doubled == 1:
            base *= 2
        elif doubled == 2:
            base *= 4
        if base >= 100:
            game_bonus = 500 if declarer_vul else 300
        else:
            game_bonus = 50
        double_bonus = 50 if doubled == 1 else (100 if doubled == 2 else 0)
        slam_bonus = 0
        if level == 6:
            slam_bonus = 750 if declarer_vul else 500
        elif level == 7:
            slam_bonus = 1500 if declarer_vul else 1000
        overtricks = tricks_made - contract_tricks
        if doubled == 0:
            ot = (30 if strain in ('NT', 'H', 'S') else 20) * overtricks
        elif doubled == 1:
            ot = (200 if declarer_vul else 100) * overtricks
        else:
            ot = (400 if declarer_vul else 200) * overtricks
        total = base + game_bonus + double_bonus + slam_bonus + ot
        return sign * total
    else:
        undertricks = contract_tricks - tricks_made
        if doubled == 0:
            ut_total = (100 if declarer_vul else 50) * undertricks
        elif doubled == 1:
            if declarer_vul:
                ut_total = 200 + 300 * (undertricks - 1) if undertricks >= 1 else 0
            else:
                ut_total = 0
                for i in range(undertricks):
                    ut_total += 100 if i == 0 else (200 if i in (1, 2) else 300)
        else:
            if declarer_vul:
                ut_total = 400 + 600 * (undertricks - 1) if undertricks >= 1 else 0
            else:
                ut_total = 0
                for i in range(undertricks):
                    ut_total += 200 if i == 0 else (400 if i in (1, 2) else 600)
        return -sign * ut_total

def imp(diff):
    table = [
        (20, 0), (40, 1), (80, 2), (120, 3), (160, 4), (210, 5),
        (260, 6), (310, 7), (360, 8), (420, 9), (490, 10), (590, 11),
        (740, 12), (890, 13), (1090, 14), (1290, 15), (1490, 16),
        (1740, 17), (1990, 18), (2240, 19), (2490, 20), (2990, 21),
        (3490, 22), (3990, 23),
    ]
    a = abs(diff)
    for limit, imps in table:
        if a <= limit:
            return imps if diff > 0 else -imps
    return 24 if diff > 0 else -24

def best_balance_score(dd, vul_str):
    """
    NS balances and plays best partscore. Tries 2-of-each-suit by N or S.
    Returns (level, strain, declarer, tricks, score) for best NS outcome.

    Also considers 3-of-suit if the 2-level contract makes with overtricks
    that suggest 3-level is safe (DD tricks >= 9).
    """
    best = None
    for level in (2, 3):
        for strain in ('S', 'H', 'D', 'C'):
            for declarer in ('N', 'S'):
                tricks = dd[declarer][strain]
                vul = vul_for_seat(vul_str, declarer)
                s = score_contract(level, strain, declarer, tricks, vul, doubled=0)
                if best is None or s > best[4]:
                    best = (level, strain, declarer, tricks, s)
    return best

def standard_score(dd, vul_str):
    """1NT by W passed out, NS defends. Returns score for NS (negative if W makes)."""
    tricks = dd['W']['NT']
    vul = vul_for_seat(vul_str, 'W')
    return score_contract(1, 'NT', 'W', tricks, vul, doubled=0)

def main():
    boards = parse_boards(DD_FILE)
    print(f"Parsed {len(boards)} boards")
    boards_with_dd = [b for b in boards if 'dd' in b]
    print(f"Boards with DD: {len(boards_with_dd)}")

    h_wins = 0
    s_wins = 0
    pushes = 0
    net_imps = 0
    contract_distribution = {}
    swings = []

    for b in boards_with_dd:
        std_s = standard_score(b['dd'], b['vul'])
        balance = best_balance_score(b['dd'], b['vul'])
        hypo_s = balance[4]
        diff = hypo_s - std_s
        imps = imp(diff)
        net_imps += imps

        if imps > 0:
            h_wins += 1
        elif imps < 0:
            s_wins += 1
        else:
            pushes += 1

        key = f"{balance[0]}{balance[1]} by {balance[2]}"
        contract_distribution[key] = contract_distribution.get(key, 0) + 1

        swings.append((imps, b['board'], b['hcp_n'], b['hcp_s'], b['shape_s'],
                       std_s, balance, hypo_s))

    print()
    print("=" * 70)
    print("Mel's Rule of 2 — Pass vs Balance comparison")
    print("=" * 70)
    print(f"Hypothesis (Balance) wins: {h_wins}")
    print(f"Standard  (Pass)    wins: {s_wins}")
    print(f"Pushes:                   {pushes}")
    print(f"Net IMPs (hypothesis):    {net_imps:+d}")
    print(f"Average IMPs/deal:        {net_imps/len(boards_with_dd):+.2f}")
    print()

    print("Best balance contracts (most common):")
    for k, v in sorted(contract_distribution.items(), key=lambda x: -x[1])[:10]:
        print(f"  {k}: {v}")
    print()

    swings.sort(key=lambda x: -abs(x[0]))
    print("Top 10 biggest swings:")
    print(f"{'IMPs':<6} {'Bd':<5} {'N':<3} {'S':<3} {'S Shape':<8} {'Std$':<7} {'Balance':<14} {'Hypo$':<7}")
    for sw in swings[:10]:
        imps, bd, n, sh, ss, std, bal, hypo_s = sw
        bal_str = f"{bal[0]}{bal[1]} by {bal[2]} ({bal[3]})"
        print(f"{imps:+d}   {bd:<5} {n:<3} {sh:<3} {ss:<8} {std:<7} {bal_str:<14} {hypo_s:<7}")

    # By NS HCP ranges
    print()
    print("By NS combined HCP:")
    bins = [(15, 18), (19, 22), (23, 25)]
    for lo, hi in bins:
        rs = []
        for b in boards_with_dd:
            ns_hcp = b['hcp_n'] + b['hcp_s']
            if lo <= ns_hcp <= hi:
                std_s = standard_score(b['dd'], b['vul'])
                bal = best_balance_score(b['dd'], b['vul'])
                rs.append(imp(bal[4] - std_s))
        if rs:
            wins = sum(1 for x in rs if x > 0)
            losses = sum(1 for x in rs if x < 0)
            push = sum(1 for x in rs if x == 0)
            net = sum(rs)
            print(f"  NS {lo}-{hi}: {len(rs)} deals; H {wins} / S {losses} / P {push}; net {net:+d} IMPs")

if __name__ == '__main__':
    main()
