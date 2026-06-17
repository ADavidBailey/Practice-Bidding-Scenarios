#!/usr/bin/env python3
"""dd_line.py — trace the trainer's double-dummy auto-play line for a board so
[PLAY] decisions can be anchored on the RIGHT trick (GENERATOR-PLAY.md).

The trainer (AI-Bridge-Play-Trainer) auto-plays every seat between authored
[PLAY] decisions with DDS, and SILENTLY SKIPS a decision whose (trick, seat,
card) isn't reached on that line. So an author needs to know, before splicing,
which trick the key card actually falls on.

The trainer's policy is reproduced here as: at every ply, play the FIRST card
endplay's solve_board returns among the DD-optimal set (validated against the
one known-good decision, Finesse_Simple board 44 -> South plays the heart queen
at trick 6, win-ace-draw-trumps-then-finesse — matched exactly by this rule;
a lowest-card tie-break finds an equal-value line that finesses at trick 2 and
does NOT match the trainer).

Usage:
  python3 -P py/dd_line.py <scenario> <board> [TARGET ...]
      Trace the line; print trick/seat/card. TARGET like S:HQ or N:DA marks
      (and reports) the trick where that seat plays that card — the [PLAY]
      anchor. Multiple targets allowed.

Reads coaching-curated/<scenario>.pbn (falls back to bba-curated/).
"""
import sys, os, re
sys.path.append(os.path.dirname(__file__))
from endplay.types import Deal, Player, Denom, Card

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENOM = {'S': Denom.spades, 'H': Denom.hearts, 'D': Denom.diamonds,
         'C': Denom.clubs, 'N': Denom.nt}
PLAYER = {'N': Player.north, 'E': Player.east, 'S': Player.south, 'W': Player.west}
LHO = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
SEAT = {v: k for k, v in PLAYER.items()}
SUITS = 'SHDC'


def find_board(scn, board):
    for d in ("coaching-curated", "bba-curated"):
        path = os.path.join(ROOT, d, f"{scn}.pbn")
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8", errors="replace").read()
        # split into board chunks, locate the requested board
        chunks = re.split(r'(?=\[Board ")', txt)
        for ch in chunks:
            m = re.search(r'\[Board "([^"]+)"\]', ch)
            if m and m.group(1) == str(board):
                return ch, path
    sys.exit(f"board {board} not found in coaching-curated/ or bba-curated/ for {scn}")


def authored_lead(chunk):
    """The load-bearing pre-lead card from the board's coaching block, as a
    plain card string like 'C8'. The trainer auto-plays THIS card, so the line
    must start from it (not a fresh DDS lead)."""
    m = re.search(r'Lead the \\([SHDC])([AKQJT2-9])', chunk)
    return f"{m.group(1)}{m.group(2)}" if m else None


def trace(deal_str, strain, declarer, lead):
    from endplay.dds import solve_board
    d = Deal(deal_str)
    d.trump = DENOM[strain]
    d.first = PLAYER[LHO[declarer]]
    line = []
    if lead:
        seat = SEAT[d.curplayer]
        d.play(Card(lead))
        line.append((1, seat, _fmt(lead)))
    while sum(len(d[p]) for p in PLAYER.values()) > 0:
        card = dds_pick(d)
        n = sum(13 - len(d[p]) for p in PLAYER.values())
        line.append((n // 4 + 1, SEAT[d.curplayer], str(card)))
        d.play(card)
    return line


def dds_pick(d):
    """The trainer's auto-play card: the FIRST card at the max trick count in
    solve_board's native order. Confirmed by Trainer to be exactly
    max(solve_board(deal), key=lambda x: x[1])[0] (Python max is first-wins on
    ties). REUSE this expression — do not re-derive/re-sort the optimal set
    yourself, which can pick a different 'first' and drift."""
    from endplay.dds import solve_board
    return max(solve_board(d), key=lambda x: x[1])[0]


def decision_values(deal_str, strain, declarer, lead, target_trick):
    """Advance the auto-play line to the ply where SOUTH (declarer) is on play
    at target_trick, and return {card_str: dd_value} for South's legal cards
    there — the CORRECTNESS check (a clean finesse needs the queen strictly >
    the ace; reachability alone does not). dd_value is NS tricks-from-here."""
    from endplay.dds import solve_board
    d = Deal(deal_str)
    d.trump = DENOM[strain]
    d.first = PLAYER[LHO[declarer]]
    if lead:
        d.play(Card(lead))
    while sum(len(d[p]) for p in PLAYER.values()) > 0:
        n = sum(13 - len(d[p]) for p in PLAYER.values())
        trick = n // 4 + 1
        if SEAT[d.curplayer] == declarer and trick == target_trick:
            return {str(c): t for c, t in solve_board(d)}
        d.play(dds_pick(d))
    return {}


GLYPH = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}


def _fmt(card2):
    return f"{GLYPH[card2[0]]}{card2[1]}"


INV_GLYPH = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
RANKV = {r: i for i, r in enumerate('23456789TJQKA', 2)}


def _walk_south_following(deal_str, strain, declarer, lead):
    """Walk the auto-play line; at each ply where the DECLARER is FOLLOWING suit
    (not on lead — so forced to one suit, a clean 'which card of this suit'
    choice) with >1 legal card, yield (trick, {card_str: dd_value}). Following-
    suit is where the finesse/unblock decisions live (dummy leads toward the
    tenace, declarer plays 3rd hand); on-lead cross-suit choices are deferred."""
    from endplay.dds import solve_board
    d = Deal(deal_str)
    d.trump = DENOM[strain]
    d.first = PLAYER[LHO[declarer]]
    if lead:
        d.play(Card(lead))
    while sum(len(d[p]) for p in PLAYER.values()) > 0:
        n = sum(13 - len(d[p]) for p in PLAYER.values())
        on_lead = (n % 4 == 0)
        if SEAT[d.curplayer] == declarer and not on_lead and len(d[d.curplayer]) >= 1:
            vals = {str(c): t for c, t in solve_board(d)}
            # genuine following only: all legal cards one suit (declarer holds the
            # led suit). A void hand (discard/ruff) spans suits -> rank comparison
            # is meaningless; that's a different (discard) decision, skip it.
            if len(vals) > 1 and len({c[0] for c in vals}) == 1:
                yield n // 4 + 1, vals
        d.play(dds_pick(d))


def _clean_candidate(vals):
    """Apply the GATE's KEEP rule to a follow-suit choice and return
    (card, margin, accepts) for the teachable card, or None. card = the highest
    DD-optimal card; KEEP only if no OTHER optimal card is an honor (T-A) or
    ranks above it (Trainer's widened honor-edge); below-it optimal spots become
    +ACCEPT. margin = how much it beats the best non-optimal (wrong) card; need
    >=1 (a real penalty) and the wrong card present."""
    best = max(vals.values())
    opt = [c for c, v in vals.items() if v == best]
    nonopt = [v for v in vals.values() if v < best]
    if not nonopt:
        return None                      # nothing worse -> not a real decision
    c = max(opt, key=lambda x: RANKV[x[1:]])
    others = [o for o in opt if o != c]
    if any(RANKV[o[1:]] >= 10 for o in others):
        return None                      # a tying honor -> gate QUARANTINEs
    if any(RANKV[o[1:]] > RANKV[c[1:]] for o in others):
        return None                      # a tying higher card -> QUARANTINE
    margin = best - max(nonopt)
    if margin < 1:
        return None
    # FINESSE signal: c is an HONOR (T-A) and a HIGHER HONOR in the suit is
    # strictly worse — "finesse the lower honour (queen) instead of cashing the
    # higher one (ace), which loses a trick". This isolates finesses from
    # trivial top-card follows AND from spot-card ducks (those have c = a low
    # spot; a hold-up/duck lesson needs its own signal, deferred). All vals are
    # one suit here (genuine following).
    if RANKV[c[1:]] < 10:
        return None
    if not any(RANKV[h[1:]] > RANKV[c[1:]] and RANKV[h[1:]] >= 10 and vals[h] < best
               for h in vals):
        return None
    accepts = sorted(others, key=lambda x: -RANKV[x[1:]])
    return c, margin, accepts


def candidates(scn, max_per_board=3):
    """Pre-screen: per board, the clean follow-suit [PLAY] candidates the gate
    should KEEP, ranked by margin, capped at max_per_board. Returns
    {board: [{trick,seat,card,margin,accepts}]}. card/accepts in suit-letter
    form (e.g. 'SQ') to match the verdict/identity schema.

    Trick-1 follow-in-led-suit decisions are excluded: declarer is 4th hand to
    the opening lead, so the DD-max honour wins the trick outright, but on a
    hold-up/avoidance board ducking is the sound single-dummy play — the DD-max
    card is the anti-lesson card there (PBS-18 / TR-19)."""
    path = os.path.join(ROOT, "coaching-curated", f"{scn}.pbn")
    txt = open(path, encoding="utf-8", errors="replace").read()
    out = {}
    for ch in re.split(r'(?=\[Board ")', txt):
        bm = re.search(r'\[Board "([^"]+)"\]', ch)
        if not bm:
            continue
        dm = re.search(r'\[Deal "([^"]+)"\]', ch)
        cm = re.search(r'\[Contract "([^"]+)"\]', ch)
        dec = re.search(r'\[Declarer "([^"]+)"\]', ch)
        if not (dm and cm and dec):
            continue
        strain = cm.group(1)[1] if len(cm.group(1)) >= 2 else 'N'
        lead = authored_lead(ch)
        found = []
        for trick, vals in _walk_south_following(dm.group(1), strain, dec.group(1), lead):
            r = _clean_candidate(vals)
            if r:
                card, margin, accepts = r
                # Exclude the trick-1 follow-in-led-suit class (e.g. Choice_Of_Finesses
                # b7/b32): declarer plays 4th hand to the opening lead, so the DD-max
                # honour wins the trick outright — but on a hold-up/avoidance board the
                # sound single-dummy play is to DUCK, making that DD-max card the
                # ANTI-lesson card. Geometric + crisp, so kill it at the source rather
                # than quiz it (PBS-18 / TR-19 defense-in-depth; the gate QUARANTINEs
                # any tip-vs-card contradiction that arrives another way).
                if trick == 1 and lead and INV_GLYPH[card[0]] == lead[0]:
                    continue
                found.append({"board": bm.group(1), "trick": trick, "seat": dec.group(1),
                              "card": INV_GLYPH[card[0]] + card[1:], "margin": margin,
                              "accepts": [INV_GLYPH[a[0]] + a[1:] for a in accepts]})
        found.sort(key=lambda x: -x["margin"])
        if found:
            out[bm.group(1)] = found[:max_per_board]
    return out


def emit_candidates(scn):
    cands = candidates(scn)
    flat = [{"board": d["board"], "trick": d["trick"], "seat": d["seat"], "card": d["card"]}
            for ds in cands.values() for d in ds]
    work = os.path.join(ROOT, "coaching-curated", ".work")
    os.makedirs(work, exist_ok=True)
    p = os.path.join(work, f"{scn}-play-candidates.json")
    import json
    json.dump(flat, open(p, "w"), indent=0)
    print(f"{scn}: {len(flat)} candidate decision(s) on {len(cands)} board(s) -> {p}")
    for b, ds in sorted(cands.items(), key=lambda x: int(x[0])):
        for d in ds:
            acc = f"  +ACCEPT {d['accepts']}" if d['accepts'] else ""
            print(f"  b{b}: [PLAY {d['trick']} {d['seat']} \\{d['card']}]  margin {d['margin']}{acc}")
    return flat


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == "candidates":
        emit_candidates(sys.argv[2])
        return
    scn, board = sys.argv[1], sys.argv[2]
    targets = []
    for t in sys.argv[3:]:
        s, c = t.split(":")
        targets.append((s.upper(), GLYPH[c[0].upper()] + c[1:].upper()))
    chunk, path = find_board(scn, board)
    deal = re.search(r'\[Deal "([^"]+)"\]', chunk).group(1)
    contract = re.search(r'\[Contract "([^"]+)"\]', chunk).group(1)
    declarer = re.search(r'\[Declarer "([^"]+)"\]', chunk).group(1)
    strain = contract[1] if len(contract) >= 2 else 'N'
    lead = authored_lead(chunk)
    print(f"{scn} board {board}: {contract} by {declarer}  (from {os.path.basename(path)})")
    print(f"  deal {deal}")
    print(f"  authored opening lead: {_fmt(lead) if lead else '(none in tips)'}")
    line = trace(deal, strain, declarer, lead)
    hits = {}
    for tk, seat, card in line:
        mark = ""
        for ts, tc in targets:
            if seat == ts and card == tc:
                mark = f"   <== ANCHOR  [PLAY {tk} {ts} \\{_unglyph(card)}]"
                hits[(ts, tc)] = tk
        print(f"  trick {tk:>2}  {seat}  {card}{mark}")
    if targets:
        print("\nANCHORS:")
        for ts, tc in targets:
            tk = hits.get((ts, tc))
            esc = f"\\{_unglyph(tc)}"
            print(f"  {ts} {tc}: " +
                  (f"trick {tk}  ->  [PLAY {tk} {ts} {esc}]" if tk
                   else "NOT PLAYED on the DD line — pick a different card/seat"))


def _unglyph(card):
    inv = {v: k for k, v in GLYPH.items()}
    return inv[card[0]] + card[1:]


if __name__ == "__main__":
    main()
