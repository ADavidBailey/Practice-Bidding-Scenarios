#!/usr/bin/env python3
"""suit_quality.py — deterministic suit-solidity classifier (GIB-aligned).

Single source of truth for the suit-quality vocabulary used in coaching prose
(see coaching-curated/GENERATOR.md). The prose is written by LLM subagents; the
GENERATOR.md spec tells them the GIB definitions, but nothing ENFORCED them — so
a "solid" label could (and did — issues #29/#30) land on a suit that is not
actually solid (e.g. KQJ964 described as a "solid" suit). This module makes the
distinction checkable in code and is wired into coach.py's `validate` gate so a
mislabel can never silently ship again.

GIB suit-quality terms (https://doc.bridgebase.com/lobbynews/gib_descriptions.html),
the highest label that fits:
  - solid:  AKQ-headed and running with no loser.
            6-card: AKQJxx or AKQTxx.  7+-card: AKQxxxx.
  - strong: "strong rebiddable" — AKQ present, or 4 of the top 5 honours
            (A,K,Q,J,T), e.g. AKJTxx, KQJT9x.
  - good:   "rebiddable" — exactly 3 of the top 5 honours, e.g. KQJxxx, AQJxxx.
  - fair:   2 of the top 5 honours.
  - weak:   0-1 of the top 5 honours.

The load-bearing distinction for the weak-two lesson is solid vs. not-solid:
AKQJ65 (solid, too good for a weak two — opens at the 1 level) vs. KQJ964
(good, the textbook disciplined weak two).
"""
import re

TOP5 = "AKQJT"


def is_solid(holding: str) -> bool:
    """GIB 'solid' for a long (6+) suit: AKQ-headed and running with no loser.
    6-card needs the fourth card to be J or T (AKQJxx / AKQTxx); 7+ just needs
    the AKQ (AKQxxxx). Holding is ranks in descending order, e.g. 'AKQJ65'."""
    h = holding.upper().replace(" ", "")
    if len(h) < 6 or h[:3] != "AKQ":
        return False
    if len(h) >= 7:
        return True
    return h[3] in "JT"


def classify(holding: str) -> str:
    """Return one of solid / strong / good / fair / weak for a holding string."""
    h = holding.upper().replace(" ", "")
    if is_solid(h):
        return "solid"
    top5 = sum(1 for r in TOP5 if r in h)
    if h[:3] == "AKQ" or top5 >= 4:
        return "strong"
    if top5 == 3:
        return "good"
    if top5 == 2:
        return "fair"
    return "weak"


# ---- coaching-prose enforcement -------------------------------------------

# Suit word/symbol -> index into the S.H.D.C holding split.
_SUIT_IDX = {"spade": 0, "heart": 1, "diamond": 2, "club": 3,
             "S": 0, "H": 1, "D": 2, "C": 3}

# A "solid <suit>" claim about a whole suit: "solid six-card heart suit",
# "solid heart suit", "solid hearts", "solid \H". Deliberately NARROW so it does
# not fire on the many legitimate non-suit uses of the word — "solid sequence"
# (a KQJ lead sequence), "solid trumps", "solid values", "solid winners",
# "solid lead", "solid game values". We only look at "solid" immediately
# qualifying a suit NAME (optionally a length) or a suit SYMBOL, and never when
# the next word is "sequence".
_SOLID_SUIT_RE = re.compile(
    r"solid\s+"
    r"(?:(?:six|seven|eight|6|7|8)[-\s]card\s+)?"   # optional length
    r"(?:(spade|heart|diamond|club)s?(?:\s+suit)?"  # group 1: suit word
    r"|\\([SHDC]))"                                  # group 2: suit symbol
    r"(?!\s+sequence)",
    re.IGNORECASE,
)


def _hands_from_deal(deal_str):
    """{seat: [S,H,D,C rank-strings]} from a PBN Deal string."""
    start, body = deal_str.split(":")
    order = {"N": "NESW", "E": "ESWN", "S": "SWNE", "W": "WNES"}[start.strip()]
    return {s: body.split()[i].split(".") for i, s in enumerate(order)}


def solidity_violations(pbn_path: str):
    """Scan a coaching PBN for prose that calls a SUIT 'solid' when the coached
    side (N/S) does not actually hold a solid suit there. Returns a list of
    dicts {board, suit, holding, phrase}. Conservative: only flags 'solid'
    directly qualifying a suit name/symbol, checked against the N and S
    holdings, so it never second-guesses 'solid sequence'/'solid trumps'/etc."""
    raw = open(pbn_path, encoding="utf-8", errors="replace").read()
    out = []
    for ch in re.split(r'(?=\[Board ")', raw):
        bm = re.search(r'\[Board "([^"]+)"\]', ch)
        dm = re.search(r'\[Deal "([^"]+)"\]', ch)
        cm = re.search(r"\{(.*)\}", ch, re.S)   # the coaching block
        if not (bm and dm and cm):
            continue
        hands = _hands_from_deal(dm.group(1))
        prose = cm.group(1)
        for m in _SOLID_SUIT_RE.finditer(prose):
            word, sym = m.group(1), m.group(2)
            idx = _SUIT_IDX[(word or sym).lower() if word else sym]
            # The claim is about the coached side's suit; accept it if EITHER
            # North or South actually holds a solid suit there.
            if any(is_solid("".join(hands[s][idx])) for s in ("N", "S")):
                continue
            ns_hold = " / ".join(f"{s}:{''.join(hands[s][idx]) or '-'}"
                                 for s in ("N", "S"))
            out.append({"board": bm.group(1),
                        "suit": "SHDC"[idx],
                        "holding": ns_hold,
                        "phrase": m.group(0)})
    return out


def solid_suit_positions(pbn_path: str, protect_first: int = 4):
    """For a bidding lesson served in file order, find boards whose coached side
    (N/S) holds a SOLID 6+-card suit — i.e. a hand too good for a weak two that
    opens at the 1 level. Returns [(served_position, board, seat, holding)].
    Used to keep such 'upgrade' boards out of the opening slots (issue #29: the
    solid AKQJ65 hand should sit beyond board 4, not lead the lesson)."""
    raw = open(pbn_path, encoding="utf-8", errors="replace").read()
    found = []
    pos = 0
    for ch in re.split(r'(?=\[Board ")', raw):
        bm = re.search(r'\[Board "([^"]+)"\]', ch)
        dm = re.search(r'\[Deal "([^"]+)"\]', ch)
        if not (bm and dm):
            continue
        pos += 1
        hands = _hands_from_deal(dm.group(1))
        for s in ("N", "S"):
            for idx in range(4):
                hold = "".join(hands[s][idx])
                if len(hold) >= 6 and is_solid(hold):
                    found.append((pos, bm.group(1), s, "SHDC"[idx] + hold))
    return found


if __name__ == "__main__":
    import sys, os
    args = sys.argv[1:]
    if not args:
        # self-test of the classifier on the canonical examples
        for h, want in [("AKQJ65", "solid"), ("AKQ8765", "solid"),
                        ("AKQ952", "strong"), ("KQJ964", "good"),
                        ("AKJT73", "strong"), ("KQ6542", "fair"),
                        ("J84321", "weak")]:
            got = classify(h)
            print(f"  {h:8} -> {got:7} {'OK' if got == want else 'EXPECTED ' + want}")
        sys.exit(0)
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total = 0
    for scn in args:
        path = os.path.join(ROOT, "coaching-curated", f"{scn}.pbn")
        if not os.path.exists(path):
            path = os.path.join(ROOT, "coaching", f"{scn}.pbn")
        if not os.path.exists(path):
            print(f"{scn}: no coaching PBN found"); continue
        viol = solidity_violations(path)
        total += len(viol)
        for v in viol:
            print(f"  {scn} b{v['board']}: '{v['phrase']}' but {v['suit']} "
                  f"holdings are {v['holding']} (not solid)")
        # Ordering lint: report solid-suit ('upgrade') boards and their served
        # position; flag any that lead the lesson (issue #29 policy: beyond #4).
        early = []
        for posn, board, seat, hold in solid_suit_positions(path):
            tag = " <-- in first 4!" if posn <= 4 else ""
            print(f"  {scn} b{board}: solid suit {seat}:{hold} served at "
                  f"position {posn}{tag}")
            if posn <= 4:
                early.append(board)
        total += len(early)
        print(f"{scn}: {len(viol)} suit-solidity issue(s), "
              f"{len(early)} solid-suit board(s) in first 4")
    sys.exit(1 if total else 0)
