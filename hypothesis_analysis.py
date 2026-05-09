#!/usr/bin/env python3
"""
Compares BBA's actual contract scores vs the hypothesis counterfactual
(partner bids NT directly based on HCP) for the 1m-1_2_or_3_NT scenario.
"""

import re
from pathlib import Path

DD_FILE = Path("/tmp/dd_analysis.pbn")

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
        d['hcp_n'], d['hcp_e'], d['hcp_s'], d['hcp_w'] = (int(x) for x in m.groups())
        m = re.search(r'\[Declarer "(\w+)"\]', b)
        d['declarer'] = m.group(1)
        m = re.search(r'\[Contract "([^"]+)"\]', b)
        d['contract'] = m.group(1)
        m = re.search(r'\[Result "(\d+)"\]', b)
        d['result'] = int(m.group(1))
        m = re.search(r'\[Score "NS ([-\d]+)"\]', b)
        d['actual_score'] = int(m.group(1))
        # OptimumResultTable: NT S H D C; rows N S E W
        m = re.search(r'\[OptimumResultTable "([^"]+)"\]', b)
        if m:
            tbl = m.group(1).replace('\\n', '\n')
            lines = tbl.strip().split('\n')
            # header: NT S H D C
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
    """Returns True if seat is vulnerable."""
    if vul_str == 'All':
        return True
    if vul_str == 'None':
        return False
    if vul_str == 'NS':
        return seat in ('N', 'S')
    if vul_str == 'EW':
        return seat in ('E', 'W')
    return False

def score_nt_contract(level, tricks_made, vul):
    """Score for NT contract by NS, given level (1-7), tricks made, vulnerability."""
    contract_tricks = level + 6
    if tricks_made >= contract_tricks:
        # Made or overtricks
        # Contract trick value: 40 for 1st, 30 each subsequent NT
        contract_score = 40 + 30 * (level - 1)
        # Overtricks at 30 each
        overtricks = tricks_made - contract_tricks
        ot_score = 30 * overtricks
        # Bonus
        if contract_score >= 100:
            # Game
            game_bonus = 500 if vul else 300
        else:
            game_bonus = 50  # Partial
        # Slam
        slam_bonus = 0
        if level == 6:
            slam_bonus = 750 if vul else 500
        elif level == 7:
            slam_bonus = 1500 if vul else 1000
        return contract_score + ot_score + game_bonus + slam_bonus
    else:
        # Undertricks (undoubled)
        undertricks = contract_tricks - tricks_made
        if vul:
            return -100 * undertricks
        else:
            return -50 * undertricks

def hypothesis_contract(hcp_n, hcp_s):
    """
    Hypothesis: partner bids 1NT/2NT/3NT directly based on N's HCP.
    Then opener decides final level based on combined HCP.
    Returns (level, declarer='N').

    Bidding logic:
    - N's NT bid level (1, 2, or 3) based on hcp_n
    - Combined HCP determines final level:
      - 6NT if combined >= 33
      - 3NT if combined >= 25 (game)
      - 2NT if combined 23-24 (max partial)
      - 1NT if combined < 23
      - But always at least the level N bid
    """
    combined = hcp_n + hcp_s
    if hcp_n < 6:
        return None  # Out of test range
    if hcp_n >= 6 and hcp_n <= 9:
        n_bid = 1
    elif hcp_n >= 10 and hcp_n <= 12:
        n_bid = 2
    elif hcp_n >= 13 and hcp_n <= 15:
        n_bid = 3
    else:
        return None  # Above test range

    # Determine final level by combined HCP
    if combined >= 33:
        final = 6
    elif combined >= 25:
        final = 3
    elif combined >= 23:
        final = 2
    else:
        final = 1

    # But never below partner's bid
    final = max(final, n_bid)
    return final  # Always declared by N in hypothesis path

def imp(diff):
    """Convert score difference to IMPs (standard table)."""
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

def parse_contract(contract_str):
    """Parse contract like '3N', '4S', '6DX', '1SXX' into (level, strain, doubled).
    Returns (level, strain, doubled) where strain is 'NT'/'S'/'H'/'D'/'C'.
    Returns None for "Pass" contracts."""
    if contract_str == 'Pass' or not contract_str:
        return None
    m = re.match(r'^(\d)([NSHDC])(X{0,2})$', contract_str)
    if not m:
        return None
    level = int(m.group(1))
    s = m.group(2)
    strain = 'NT' if s == 'N' else s
    doubled = len(m.group(3))
    return (level, strain, doubled)

def score_suit_contract(level, strain, declarer, tricks_made, vul, doubled=0):
    """Score for a suit/NT contract by NS, given level, strain, declarer, tricks, vul, doubled.
    Returns NS score (positive if NS contract makes; negative if EW makes or NS undertricks)."""
    contract_tricks = level + 6
    is_ns = declarer in ('N', 'S')
    sign = 1 if is_ns else -1
    declarer_vul = vul

    if tricks_made >= contract_tricks:
        # Made
        if strain == 'NT':
            base = 40 + 30 * (level - 1)
        elif strain in ('H', 'S'):
            base = 30 * level
        else:  # C, D
            base = 20 * level
        if doubled == 1:
            base *= 2
        elif doubled == 2:
            base *= 4
        # Game/partial bonus
        if base >= 100:
            game_bonus = 500 if declarer_vul else 300
        else:
            game_bonus = 50
        # Doubled bonus (for making doubled): 50
        double_bonus = 50 if doubled == 1 else (100 if doubled == 2 else 0)
        # Slam
        slam_bonus = 0
        if level == 6:
            slam_bonus = 750 if declarer_vul else 500
        elif level == 7:
            slam_bonus = 1500 if declarer_vul else 1000
        # Overtricks
        overtricks = tricks_made - contract_tricks
        if doubled == 0:
            if strain == 'NT' or strain in ('H', 'S'):
                ot = 30 * overtricks
            else:
                ot = 20 * overtricks
        elif doubled == 1:
            ot = (200 if declarer_vul else 100) * overtricks
        else:  # XX
            ot = (400 if declarer_vul else 200) * overtricks
        total = base + game_bonus + double_bonus + slam_bonus + ot
        return sign * total
    else:
        # Undertricks
        undertricks = contract_tricks - tricks_made
        if doubled == 0:
            ut_total = (100 if declarer_vul else 50) * undertricks
        elif doubled == 1:
            # 200/300/300/300... vul; 100/200/200/300/... NV
            if declarer_vul:
                ut_total = 200 + 300 * (undertricks - 1) if undertricks >= 1 else 0
            else:
                ut_total = 0
                for i in range(undertricks):
                    if i == 0:
                        ut_total += 100
                    elif i in (1, 2):
                        ut_total += 200
                    else:
                        ut_total += 300
        else:  # XX double = 2x doubled
            if declarer_vul:
                ut_total = 400 + 600 * (undertricks - 1) if undertricks >= 1 else 0
            else:
                ut_total = 0
                for i in range(undertricks):
                    if i == 0:
                        ut_total += 200
                    elif i in (1, 2):
                        ut_total += 400
                    else:
                        ut_total += 600
        return -sign * ut_total

def main():
    boards = parse_boards(DD_FILE)
    print(f"Parsed {len(boards)} boards")

    # Filter to deals where partner is in 6-15 HCP range (the hypothesis test range)
    test_boards = [b for b in boards if 6 <= b['hcp_n'] <= 15]
    print(f"Boards in test range (N HCP 6-15): {len(test_boards)}")

    results_by_range = {
        '6-9': {'h_wins': 0, 's_wins': 0, 'pushes': 0, 'h_imps': 0, 's_imps': 0},
        '10-12': {'h_wins': 0, 's_wins': 0, 'pushes': 0, 'h_imps': 0, 's_imps': 0},
        '13-15': {'h_wins': 0, 's_wins': 0, 'pushes': 0, 'h_imps': 0, 's_imps': 0},
    }
    overall = {'h_wins': 0, 's_wins': 0, 'pushes': 0, 'net_imps': 0}

    for b in test_boards:
        hcp_n = b['hcp_n']
        hcp_s = b['hcp_s']
        if hcp_n <= 9:
            range_key = '6-9'
        elif hcp_n <= 12:
            range_key = '10-12'
        else:
            range_key = '13-15'

        # Standard score: BBA's contract scored using DD trick count for its declarer/strain
        c = parse_contract(b['contract'])
        if c is None:
            continue
        s_level, s_strain, s_doubled = c
        s_decl = b['declarer']
        s_tricks = b['dd'][s_decl][s_strain]
        s_vul = vul_for_seat(b['vul'], s_decl)
        std_score = score_suit_contract(s_level, s_strain, s_decl, s_tricks, s_vul, s_doubled)

        # Hypothesis score: NT by N at the level determined by combined HCP
        hypo_level = hypothesis_contract(hcp_n, hcp_s)
        if hypo_level is None:
            continue
        hypo_tricks = b['dd']['N']['NT']
        hypo_vul = vul_for_seat(b['vul'], 'N')
        hypo_score = score_nt_contract(hypo_level, hypo_tricks, hypo_vul)

        diff = hypo_score - std_score
        imps = imp(diff)
        overall['net_imps'] += imps

        if abs(imps) == 0:
            overall['pushes'] += 1
            results_by_range[range_key]['pushes'] += 1
        elif imps > 0:
            overall['h_wins'] += 1
            results_by_range[range_key]['h_wins'] += 1
            results_by_range[range_key]['h_imps'] += imps
        else:
            overall['s_wins'] += 1
            results_by_range[range_key]['s_wins'] += 1
            results_by_range[range_key]['s_imps'] += -imps

    print()
    print("=" * 70)
    print("Results by HCP range:")
    print("=" * 70)
    print(f"{'Range':<8} {'H wins':<8} {'S wins':<8} {'Pushes':<8} {'H IMPs':<8} {'S IMPs':<8} {'Net':<8}")
    for rng in ['6-9', '10-12', '13-15']:
        r = results_by_range[rng]
        net = r['h_imps'] - r['s_imps']
        print(f"{rng:<8} {r['h_wins']:<8} {r['s_wins']:<8} {r['pushes']:<8} {r['h_imps']:<8} {r['s_imps']:<8} {net:+d}")
    print()
    print("=" * 70)
    print("Overall:")
    print("=" * 70)
    print(f"Hypothesis wins: {overall['h_wins']}")
    print(f"Standard wins:   {overall['s_wins']}")
    print(f"Pushes:          {overall['pushes']}")
    print(f"Net IMPs (hypothesis): {overall['net_imps']:+d}")
    print()

    # Sample some big swings for context
    swings = []
    for b in test_boards:
        hypo_level = hypothesis_contract(b['hcp_n'], b['hcp_s'])
        if hypo_level is None:
            continue
        hypo_tricks = b['dd']['N']['NT']
        hypo_vul = vul_for_seat(b['vul'], 'N')
        hypo_score = score_nt_contract(hypo_level, hypo_tricks, hypo_vul)
        diff = hypo_score - b['actual_score']
        imps = imp(diff)
        swings.append((imps, b['board'], b['hcp_n'], b['hcp_s'], b['contract'], b['actual_score'], hypo_level, hypo_tricks, hypo_score))

    # Recompute swings with DD-fair scoring
    swings = []
    for b in test_boards:
        c = parse_contract(b['contract'])
        if c is None:
            continue
        s_level, s_strain, s_doubled = c
        s_decl = b['declarer']
        s_tricks = b['dd'][s_decl][s_strain]
        s_vul = vul_for_seat(b['vul'], s_decl)
        std_score = score_suit_contract(s_level, s_strain, s_decl, s_tricks, s_vul, s_doubled)
        hypo_level = hypothesis_contract(b['hcp_n'], b['hcp_s'])
        if hypo_level is None:
            continue
        hypo_tricks = b['dd']['N']['NT']
        hypo_vul = vul_for_seat(b['vul'], 'N')
        hypo_score = score_nt_contract(hypo_level, hypo_tricks, hypo_vul)
        diff = hypo_score - std_score
        imps = imp(diff)
        swings.append((imps, b['board'], b['hcp_n'], b['hcp_s'], b['contract'], std_score, hypo_level, hypo_tricks, hypo_score))

    swings.sort(key=lambda x: -abs(x[0]))
    print("Top 10 biggest swings:")
    print(f"{'IMPs':<6} {'Bd':<4} {'N':<3} {'S':<3} {'BBA':<8} {'Std$':<7} {'Hypo':<6} {'NT_t':<5} {'Hypo$':<7}")
    for s in swings[:10]:
        imps, bd, n, sh, contract, std, lvl, t, hypo_s = s
        print(f"{imps:+d}   {bd:<4} {n:<3} {sh:<3} {contract:<8} {std:<7} {lvl}NT    {t:<5} {hypo_s:<7}")

if __name__ == '__main__':
    main()
