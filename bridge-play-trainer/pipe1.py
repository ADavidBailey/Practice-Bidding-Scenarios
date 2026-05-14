"""
Pipe 1 — standalone deal walker.

Loads a deal from a BBA-output PBN (auction + contract), determines declarer,
then walks all 13 tricks with DDS picking the optimal card for every seat.
No user input, no Claude. Validates state tracking.

Run from repo root:
    python3 bridge-play-trainer/pipe1.py
    python3 bridge-play-trainer/pipe1.py --scenario Major_Suit_Fit --board 0
"""

import argparse
import sys
from pathlib import Path

from endplay.types import Player, Denom, Penalty
from endplay.dds import solve_board
from endplay.parsers import pbn

REPO_ROOT = Path(__file__).resolve().parent.parent
BBA_DIR = REPO_ROOT / "bba"

SEAT_LETTER = {Player.north: "N", Player.east: "E", Player.south: "S", Player.west: "W"}
DENOM_LETTER = {Denom.spades: "S", Denom.hearts: "H", Denom.diamonds: "D", Denom.clubs: "C", Denom.nt: "NT"}
DENOM_SYM = {Denom.spades: "♠", Denom.hearts: "♥", Denom.diamonds: "♦", Denom.clubs: "♣", Denom.nt: "NT"}


def left_of(p: Player) -> Player:
    return Player((int(p) + 1) % 4)


def parse_contract(contract_str: str):
    """'5H' -> (5, Denom.hearts). '4SX' -> (4, Denom.spades). 'Pass' -> None."""
    if not contract_str or contract_str in ("?", "Pass"):
        return None
    level = int(contract_str[0])
    strain = contract_str[1:].rstrip("X")
    denom_map = {"S": Denom.spades, "H": Denom.hearts, "D": Denom.diamonds, "C": Denom.clubs, "N": Denom.nt, "NT": Denom.nt}
    return level, denom_map[strain]


def derive_declarer(auction, dealer: Player, trump: Denom) -> Player:
    """Declarer = first player on the contract-winning side to name the trump strain."""
    seat = dealer
    last_bidder = None
    final_strain_bidders = {}
    for call in auction:
        if not isinstance(call, Penalty.__class__) and hasattr(call, "denom"):
            last_bidder = seat
            side = "NS" if seat in (Player.north, Player.south) else "EW"
            final_strain_bidders.setdefault((side, call.denom), seat)
        seat = left_of(seat)

    if last_bidder is None:
        raise ValueError("All-pass auction")
    winning_side = "NS" if last_bidder in (Player.north, Player.south) else "EW"
    return final_strain_bidders[(winning_side, trump)]


def render_hand(hand) -> str:
    """North-style 4-line block."""
    return "\n".join([
        f"  ♠ {' '.join(r.abbr for r in hand.spades) or '-'}",
        f"  ♥ {' '.join(r.abbr for r in hand.hearts) or '-'}",
        f"  ♦ {' '.join(r.abbr for r in hand.diamonds) or '-'}",
        f"  ♣ {' '.join(r.abbr for r in hand.clubs) or '-'}",
    ])


def play_deal(board, verbose: bool = True) -> dict:
    deal = board.deal
    contract_str = board.info.get("Contract", "?")
    parsed = parse_contract(contract_str)
    if parsed is None:
        return {"error": f"no playable contract: {contract_str}"}
    level, trump = parsed
    dealer = Player(board.dealer) if board.dealer is not None else Player.north
    declarer = derive_declarer(board.auction, dealer, trump)
    opening_leader = left_of(declarer)
    tricks_needed = 6 + level

    deal.first = opening_leader
    deal.trump = trump

    if verbose:
        print(f"\n=== {board.info.get('Event', '?')} board {board.board_num} ===")
        print(f"Contract: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]}   "
              f"Dealer: {SEAT_LETTER[dealer]}   Leader: {SEAT_LETTER[opening_leader]}\n")
        for seat in (Player.north, Player.east, Player.south, Player.west):
            hand = [deal.north, deal.east, deal.south, deal.west][int(seat)]
            print(f"{SEAT_LETTER[seat]}:")
            print(render_hand(hand))
            print()

    declarer_side = {Player.north, Player.south} if declarer in (Player.north, Player.south) else {Player.east, Player.west}
    ns_tricks = ew_tricks = 0

    for trick_num in range(1, 14):
        plays = []
        leader = deal.first
        for _ in range(4):
            seat = deal.curplayer
            sb = solve_board(deal)
            best_card, _max_tricks = max(sb, key=lambda x: x[1])
            plays.append((seat, best_card))
            deal.play(best_card)
        winner = deal.curplayer
        if winner in (Player.north, Player.south):
            ns_tricks += 1
        else:
            ew_tricks += 1

        if verbose:
            order = ", ".join(f"{SEAT_LETTER[s]}:{c}" for s, c in plays)
            print(f"Trick {trick_num:2d}  led by {SEAT_LETTER[leader]:1}  {order}   "
                  f"won by {SEAT_LETTER[winner]}   (NS:{ns_tricks} EW:{ew_tricks})")

    declarer_tricks = ns_tricks if declarer in (Player.north, Player.south) else ew_tricks
    defender_tricks = 13 - declarer_tricks
    result_offset = declarer_tricks - tricks_needed
    result_str = "=" if result_offset == 0 else (f"+{result_offset}" if result_offset > 0 else str(result_offset))

    if verbose:
        print(f"\nResult: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]} "
              f"makes {declarer_tricks} ({result_str})   "
              f"Defenders: {defender_tricks}")
    return {
        "contract": f"{level}{DENOM_LETTER[trump]}",
        "declarer": SEAT_LETTER[declarer],
        "declarer_tricks": declarer_tricks,
        "defender_tricks": defender_tricks,
        "result": result_str,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="Major_Suit_Fit", help="scenario name (without .pbn)")
    ap.add_argument("--board", type=int, default=0, help="board index (0-based)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    path = BBA_DIR / f"{args.scenario}.pbn"
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 2
    with open(path) as f:
        boards = list(pbn.load(f))
    if args.board >= len(boards):
        print(f"ERROR: board {args.board} out of range (0..{len(boards)-1})", file=sys.stderr)
        return 2

    play_deal(boards[args.board], verbose=not args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
