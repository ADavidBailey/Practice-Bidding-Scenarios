#!/usr/bin/env python3
"""Curation trial (SCRATCH, uncommitted) for Suit_Promotion, Hold_Up_3N, Choice_Of_Finesses.

Deliverable: for each scenario, flag defective curated boards (DD), size the clean
replacement pool, and (where applicable) apply a single-dummy 'technique-required'
oracle. No coaching prose is touched.
"""
from endplay.types import Deal, Denom, Player, Card
from endplay.dds import calc_dd_table, solve_board

DEN = {'C': Denom.clubs, 'D': Denom.diamonds, 'H': Denom.hearts, 'S': Denom.spades, 'N': Denom.nt}
PL  = {'N': Player.north, 'E': Player.east, 'S': Player.south, 'W': Player.west}
PART= {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
SUITS = ['S', 'H', 'D', 'C']

_dd_cache = {}
def dd(deal_str, strain, seat):
    key = deal_str
    t = _dd_cache.get(key)
    if t is None:
        t = calc_dd_table(Deal(deal_str)); _dd_cache[key] = t
    return t[strain, PL[seat]]

def parse(path):
    out = []; d = c = dec = bn = None
    for line in open(path):
        if line.startswith("[Board "): bn = line.split('"')[1]
        elif line.startswith("[Deal "): d = line.split('"')[1]
        elif line.startswith("[Contract "): c = line.split('"')[1]
        elif line.startswith("[Declarer "): dec = line.split('"')[1]
        if line.strip() == "" and d:
            out.append(dict(bn=bn, deal=d, con=c, dec=dec)); d = c = dec = bn = None
    if d: out.append(dict(bn=bn, deal=d, con=c, dec=dec))
    return out

def hands(deal_str):
    body = deal_str.split(":")[1].split()
    return {s: body[i].split('.') for i, s in enumerate(['N', 'E', 'S', 'W'])}

def need_of(con):  # tricks needed
    return 6 + int(con[0])

# ---- defect classification (DD as negative filter) ----
def classify(b):
    strain = DEN[b['con'][1]]; need = need_of(b['con'])
    d_decl = dd(b['deal'], strain, b['dec'])
    d_part = dd(b['deal'], strain, PART[b['dec']])
    if d_decl >= need: return 'ok', d_decl, d_part
    if d_part >= need: return 'wrong_sided', d_decl, d_part
    return 'down_both', d_decl, d_part

# ---- Hold-up single-dummy oracle: does winning round 1 of the danger suit fail? ----
def lowest(holding):           # holdings are high->low in PBN
    return holding[-1] if holding else None
def lowest_overall(seat_suits):
    RANK = "AKQJT98765432"
    best = None
    for si, su in enumerate(SUITS):
        if seat_suits[si]:
            r = seat_suits[si][-1]
            if best is None or RANK.index(r) > RANK.index(best[1]):
                best = (su, r)
    return best[0] + best[1]

def holdup_required(deal_str):
    """Return True if 3NT makes DD from South but FAILS if declarer wins the
    first round of the danger suit (i.e. the hold-up is necessary). None if no
    hold-up theme / not testable; False if not required."""
    h = hands(deal_str)
    # danger suit: N-S hold A but not K (single stopper), E-W length >= 5
    cands = []
    for si, su in enumerate(SUITS):
        ns = h['N'][si] + h['S'][si]
        ew = len(h['E'][si]) + len(h['W'][si])
        if 'A' in ns and 'K' not in ns and ew >= 5:
            cands.append((ew, su, si))
    if not cands: return None
    cands.sort(reverse=True)
    _, su, si = cands[0]
    if dd(deal_str, Denom.nt, 'S') < 9: return False
    if not h['W'][si]: return None                       # leader can't lead it
    ace_holder = 'N' if 'A' in h['N'][si] else 'S'       # who holds the stopper
    d = Deal(deal_str); d.trump = Denom.nt; d.first = Player.west
    # trick 1, rotation W,N,E,S: leader low; ace-holder wins with A; others low/discard
    for seat in ['W', 'N', 'E', 'S']:
        if seat == ace_holder:
            card = su + 'A'
        elif h[seat][si]:
            card = su + lowest(h[seat][si])
        else:
            card = lowest_overall(h[seat])
        d.play(Card(card))
    # winner (ace_holder, declarer side) now on lead; max tricks declarer can still take
    decl_more = max(t for _, t in solve_board(d))
    return (1 + decl_more) < 9

# ---- by-force test (Suit_Promotion): makeable regardless of honor location ----
def swap_ew(deal_str):
    h = hands(deal_str)
    e = ['.'.join(h['E'][i] for i in range(4))]  # placeholder
    # rebuild deal string N E S W with E and W swapped
    def hs(seat): return '.'.join(h[seat])
    return "N:" + " ".join([hs('N'), hs('W'), hs('S'), hs('E')])

def by_force(deal_str, con):
    strain = DEN[con[1]]; need = need_of(con)
    if dd(deal_str, strain, 'S') < need: return False
    # makeable from South even with E/W honors flipped -> not finesse-dependent
    return dd(swap_ew(deal_str), strain, 'S') >= need

# ============================ run the trial ============================
def report(scn, target_con, mode):
    cur = parse(f"coaching/{scn}.pbn")
    pool = parse(f"bba-filtered/{scn}.pbn")
    # 1) current set quality
    buckets = {'ok': [], 'wrong_sided': [], 'down_both': []}
    for b in cur:
        if not b['con']: continue
        k, dde, ddp = classify(b)
        buckets[k].append((b['bn'], b['con'], dde, ddp))
    print(f"\n========== {scn} ==========")
    print(f"curated n={len(cur)}  ok={len(buckets['ok'])}  "
          f"wrong_sided={len(buckets['wrong_sided'])}  down_both={len(buckets['down_both'])}")
    for k in ('wrong_sided', 'down_both'):
        if buckets[k]:
            print(f"  {k}: " + ", ".join(f"b{bn}({con} S={de}/N-or-part={dp})" for bn, con, de, dp in buckets[k]))
    defects = len(buckets['wrong_sided']) + len(buckets['down_both'])

    # 2) pool candidates (target = 3NT from South), gated by technique
    nt, need = Denom.nt, 9
    makeable = [b for b in pool if dd(b['deal'], nt, 'S') >= need]
    print(f"pool n={len(pool)}  3NT makeable-from-South={len(makeable)}")
    if mode == 'holdup':
        req = [b for b in makeable if holdup_required(b['deal']) is True]
        print(f"  ...of those, hold-up REQUIRED (single-dummy oracle): {len(req)}")
        # validate oracle on curated 'ok' boards
        cur_ok = [b for b in cur if b['con'] and classify(b)[0] == 'ok']
        val = sum(1 for b in cur_ok if holdup_required(b['deal']) is True)
        print(f"  oracle validation: {val}/{len(cur_ok)} of sound curated boards flagged hold-up-required")
        print(f"  => {defects} defective curated boards to replace; clean technique-pool = {len(req)}")
    elif mode == 'byforce':
        bf = [b for b in makeable if by_force(b['deal'], '3N')]
        print(f"  ...of those, makeable BY FORCE (E/W-swap robust): {len(bf)}")
        cur_ok = [b for b in cur if b['con'] and classify(b)[0] == 'ok' and b['con'][1] == 'N']
        val = sum(1 for b in cur_ok if by_force(b['deal'], '3N'))
        print(f"  oracle validation: {val}/{len(cur_ok)} of sound curated 3NT boards are by-force")
        print(f"  => {defects} defective curated boards to replace; clean by-force pool = {len(bf)}")
    else:  # choice — structural avoidance shape (full single-dummy oracle = next build)
        shaped = []
        for b in makeable:
            h = hands(b['deal'])
            one_stop = any('A' in (h['N'][i] + h['S'][i]) and 'K' not in (h['N'][i] + h['S'][i])
                           and len(h['E'][i]) + len(h['W'][i]) >= 5 for i in range(4))
            tenace = sum(1 for i in range(4)
                         for hd in [h['N'][i], h['S'][i]]
                         if ('A' in hd and 'Q' in hd and 'K' not in hd) or ('K' in hd and 'J' in hd and 'Q' not in hd))
            if one_stop and tenace >= 1: shaped.append(b)
        print(f"  ...of those, avoidance-shaped (1 stopper + >=1 finesse tenace): {len(shaped)}")
        print(f"  => {defects} defective curated boards; avoidance-shaped pool = {len(shaped)} "
              f"(full single-dummy 'wrong-finesse-fails' oracle = next build)")

if __name__ == "__main__":
    report("Suit_Promotion", "3N", "byforce")
    report("Hold_Up_3N", "3N", "holdup")
    report("Choice_Of_Finesses", "3N", "choice")
    print("\n(scratch script: curation_trial.py — uncommitted)")
