#!/usr/bin/env python3
"""
Scan all bba/*.pbn files and find deals that look like endplay candidates.

Endplay heuristic (v1):
- South is declarer in a 4-of-major contract (4H or 4S).
- Declarer's side has an AJ tenace in a side suit (A in declarer or dummy,
  J in declarer or dummy, K somewhere in declarer's side, Q in opps).
- Declarer's side has solid honors in at least one OTHER side suit (AK or
  AKQ), so stripping is feasible.

Output: bba/Found_Endplay.pbn (treated as a normal scenario by the trainer).
"""

from pathlib import Path
import sys

from endplay.types import Player, Denom, Rank
from endplay.parsers import pbn

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BBA_DIR = REPO_ROOT / "bba"
OUTPUT_PATH = BBA_DIR / "Found_Endplay.pbn"

SEAT_LETTER = {Player.north: "N", Player.east: "E", Player.south: "S", Player.west: "W"}
DENOM_LETTER = {Denom.spades: "S", Denom.hearts: "H", Denom.diamonds: "D", Denom.clubs: "C", Denom.nt: "NT"}


def hand_for(deal, seat: Player):
    return [deal.north, deal.east, deal.south, deal.west][int(seat)]


def suit_ranks(hand, suit_attr: str):
    return {r.abbr for r in getattr(hand, suit_attr)}


def parse_contract(s):
    if not s or s == "?" or s == "Pass":
        return None
    level = int(s[0])
    strain = s[1:].rstrip("X")
    m = {"S": Denom.spades, "H": Denom.hearts, "D": Denom.diamonds, "C": Denom.clubs,
         "N": Denom.nt, "NT": Denom.nt}
    return level, m[strain]


def derive_declarer(auction, dealer, trump):
    seat = dealer
    last_bidder = None
    final = {}
    for call in auction:
        if hasattr(call, "denom"):
            last_bidder = seat
            side = "NS" if seat in (Player.north, Player.south) else "EW"
            final.setdefault((side, call.denom), seat)
        seat = Player((int(seat) + 1) % 4)
    winning_side = "NS" if last_bidder in (Player.north, Player.south) else "EW"
    return final.get((winning_side, trump))


SUIT_ATTRS = {"S": "spades", "H": "hearts", "D": "diamonds", "C": "clubs"}


def has_aj_tenace(declarer_hand, dummy_hand, suit_letter: str):
    """Returns True if NS holds A and J of the suit, plus K, but not Q.
    This is the AJ-vs-K tenace pattern an endplay can exploit."""
    attr = SUIT_ATTRS[suit_letter]
    decl_ranks = suit_ranks(declarer_hand, attr)
    dum_ranks = suit_ranks(dummy_hand, attr)
    combined = decl_ranks | dum_ranks
    return "A" in combined and "J" in combined and "K" in combined and "Q" not in combined


def has_solid_strip_suit(declarer_hand, dummy_hand, suit_letter: str):
    """Returns True if NS has AK (or better) of a suit — usable for stripping."""
    attr = SUIT_ATTRS[suit_letter]
    combined = suit_ranks(declarer_hand, attr) | suit_ranks(dummy_hand, attr)
    return "A" in combined and "K" in combined


def is_endplay_candidate(deal, contract_str, declarer):
    parsed = parse_contract(contract_str)
    if parsed is None:
        return False
    level, trump = parsed
    if level != 4 or trump not in (Denom.spades, Denom.hearts):
        return False
    if declarer != Player.south:
        return False
    declarer_hand = hand_for(deal, Player.south)
    dummy_hand = hand_for(deal, Player.north)
    trump_letter = DENOM_LETTER[trump]
    side_suits = [s for s in "SHDC" if s != trump_letter]
    # Need an AJ tenace in at least one side suit
    tenace_suits = [s for s in side_suits if has_aj_tenace(declarer_hand, dummy_hand, s)]
    if not tenace_suits:
        return False
    # Need a different side suit with solid AK for stripping
    other_side_suits = [s for s in side_suits if s not in tenace_suits]
    if not any(has_solid_strip_suit(declarer_hand, dummy_hand, s) for s in other_side_suits):
        return False
    return True


def find_candidates():
    matches = []
    files_scanned = 0
    deals_scanned = 0
    for path in sorted(BBA_DIR.glob("*.pbn")):
        if path.stem.startswith("Found_") or path.stem.startswith("-"):
            continue
        files_scanned += 1
        try:
            with open(path) as f:
                boards = list(pbn.load(f))
        except Exception:
            continue
        for board in boards:
            deals_scanned += 1
            contract = board.info.get("Contract", "?")
            parsed = parse_contract(contract)
            if parsed is None:
                continue
            level, trump = parsed
            dealer = Player(board.dealer) if board.dealer is not None else Player.north
            declarer = derive_declarer(board.auction, dealer, trump)
            if declarer is None:
                continue
            if is_endplay_candidate(board.deal, contract, declarer):
                # Stash the derived declarer so the writer doesn't have to redo it.
                board.info["Declarer"] = SEAT_LETTER[declarer]
                matches.append(board)
    return matches, files_scanned, deals_scanned


def write_pbn(boards, out_path):
    """Write boards out in PBN format. We use endplay's own writer if it works,
    otherwise hand-roll a minimal PBN."""
    try:
        # endplay does not expose a clean write API. Hand-roll instead.
        raise NotImplementedError
    except NotImplementedError:
        pass

    lines = []
    for i, board in enumerate(boards, start=1):
        d = board.deal
        info = board.info
        contract = info.get("Contract", "?")
        declarer = info.get("Declarer", "?")
        dealer = SEAT_LETTER[Player(board.dealer)] if board.dealer is not None else "N"

        def suit_str(hand_attr, ranks_iter):
            return "".join(r.abbr for r in ranks_iter)

        hands = {}
        for seat, hand in (("N", d.north), ("E", d.east), ("S", d.south), ("W", d.west)):
            hands[seat] = ".".join(
                "".join(r.abbr for r in getattr(hand, attr))
                for attr in ("spades", "hearts", "diamonds", "clubs")
            )

        # Deal tag: "N:NHand EHand SHand WHand"
        deal_str = f"N:{hands['N']} {hands['E']} {hands['S']} {hands['W']}"

        lines.append(f'[Event "Found_Endplay"]')
        lines.append(f'[Board "{i}"]')
        lines.append(f'[Dealer "{dealer}"]')
        lines.append('[Vulnerable "None"]')
        lines.append(f'[Deal "{deal_str}"]')
        lines.append(f'[Declarer "{declarer}"]')
        lines.append(f'[Contract "{contract}"]')

        # Reproduce the auction
        lines.append(f'[Auction "{dealer}"]')
        auction_lines = []
        row = []
        for call in board.auction:
            if hasattr(call, "denom"):
                if call.denom == Denom.nt:
                    txt = f"{call.level}NT"
                else:
                    txt = f"{call.level}{DENOM_LETTER[call.denom]}"
            else:
                penalty = getattr(call, "penalty", None)
                pn = getattr(penalty, "name", None) if penalty is not None else None
                txt = {"passed": "Pass", "doubled": "X", "redoubled": "XX"}.get(pn, "Pass")
            row.append(txt)
            if len(row) == 4:
                auction_lines.append("  ".join(f"{r:5s}" for r in row).rstrip())
                row = []
        if row:
            auction_lines.append("  ".join(f"{r:5s}" for r in row).rstrip())
        lines.extend(auction_lines)
        lines.append("")  # blank line between boards

    out_path.write_text("\n".join(lines) + "\n")


def main():
    matches, files_scanned, deals_scanned = find_candidates()
    print(f"Scanned {files_scanned} files / {deals_scanned} deals")
    print(f"Found {len(matches)} endplay candidates")
    if matches:
        # Cap at 500 to match other scenarios
        matches = matches[:500]
        write_pbn(matches, OUTPUT_PATH)
        print(f"Wrote {len(matches)} deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
