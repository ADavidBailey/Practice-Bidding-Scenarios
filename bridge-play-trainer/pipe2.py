"""
Pipe 2 — user plays declarer's cards.

User is declarer; sees own hand + dummy. Defenders are played by DDS (optimal).
Input: type a card like "SA", "as", "h10", "♥T" — or a number from the legal-moves list.

Run from repo root:
    python3 bridge-play-trainer/pipe2.py
    python3 bridge-play-trainer/pipe2.py --scenario Major_Suit_Fit --board 0
"""

import argparse
import sys
from pathlib import Path

from endplay.types import Player, Denom, Rank, Card
from endplay.dds import solve_board
from endplay.parsers import pbn

REPO_ROOT = Path(__file__).resolve().parent.parent
BBA_DIR = REPO_ROOT / "bba"

SEAT_LETTER = {Player.north: "N", Player.east: "E", Player.south: "S", Player.west: "W"}
DENOM_LETTER = {Denom.spades: "S", Denom.hearts: "H", Denom.diamonds: "D", Denom.clubs: "C", Denom.nt: "NT"}
DENOM_SYM = {Denom.spades: "♠", Denom.hearts: "♥", Denom.diamonds: "♦", Denom.clubs: "♣", Denom.nt: "NT"}
SUIT_FROM_CHAR = {"S": Denom.spades, "H": Denom.hearts, "D": Denom.diamonds, "C": Denom.clubs,
                  "♠": Denom.spades, "♥": Denom.hearts, "♦": Denom.diamonds, "♣": Denom.clubs}
RANK_FROM_CHAR = {"A": Rank.RA, "K": Rank.RK, "Q": Rank.RQ, "J": Rank.RJ, "T": Rank.RT,
                  "9": Rank.R9, "8": Rank.R8, "7": Rank.R7, "6": Rank.R6, "5": Rank.R5,
                  "4": Rank.R4, "3": Rank.R3, "2": Rank.R2}


def left_of(p: Player) -> Player:
    return Player((int(p) + 1) % 4)


def parse_contract(contract_str: str):
    if not contract_str or contract_str in ("?", "Pass"):
        return None
    level = int(contract_str[0])
    strain = contract_str[1:].rstrip("X")
    denom_map = {"S": Denom.spades, "H": Denom.hearts, "D": Denom.diamonds, "C": Denom.clubs, "N": Denom.nt, "NT": Denom.nt}
    return level, denom_map[strain]


def derive_declarer(auction, dealer: Player, trump: Denom) -> Player:
    seat = dealer
    last_bidder = None
    final_strain_bidders = {}
    for call in auction:
        if hasattr(call, "denom"):
            last_bidder = seat
            side = "NS" if seat in (Player.north, Player.south) else "EW"
            final_strain_bidders.setdefault((side, call.denom), seat)
        seat = left_of(seat)
    if last_bidder is None:
        raise ValueError("All-pass auction")
    winning_side = "NS" if last_bidder in (Player.north, Player.south) else "EW"
    return final_strain_bidders[(winning_side, trump)]


def hand_of(deal, seat: Player):
    return [deal.north, deal.east, deal.south, deal.west][int(seat)]


def render_hand(hand) -> str:
    return "\n".join([
        f"  ♠ {' '.join(r.abbr for r in hand.spades) or '-'}",
        f"  ♥ {' '.join(r.abbr for r in hand.hearts) or '-'}",
        f"  ♦ {' '.join(r.abbr for r in hand.diamonds) or '-'}",
        f"  ♣ {' '.join(r.abbr for r in hand.clubs) or '-'}",
    ])


def parse_card_input(text: str, legal):
    """Accept '1'..'N' index, 'SA', 'as', '♥T', etc."""
    t = text.strip().upper().replace(" ", "")
    if not t:
        return None
    if t.isdigit():
        i = int(t) - 1
        if 0 <= i < len(legal):
            return legal[i]
        return None
    # Try both orders: suit+rank, rank+suit
    chars = [c for c in t if c in SUIT_FROM_CHAR or c in RANK_FROM_CHAR or c == "1"]
    # Handle "10" → T
    t = t.replace("10", "T")
    if len(t) != 2:
        return None
    a, b = t[0], t[1]
    suit = rank = None
    if a in SUIT_FROM_CHAR and b in RANK_FROM_CHAR:
        suit, rank = SUIT_FROM_CHAR[a], RANK_FROM_CHAR[b]
    elif b in SUIT_FROM_CHAR and a in RANK_FROM_CHAR:
        suit, rank = SUIT_FROM_CHAR[b], RANK_FROM_CHAR[a]
    if suit is None:
        return None
    for c in legal:
        if c.suit == suit and c.rank == rank:
            return c
    return None


def format_legal(legal) -> str:
    return "  ".join(f"[{i+1}] {c}" for i, c in enumerate(legal))


def prompt_user_card(seat: Player, deal) -> Card:
    legal = list(deal.legal_moves())
    print(f"\n  Legal moves for {SEAT_LETTER[seat]}:  {format_legal(legal)}")
    while True:
        try:
            text = input(f"  Play for {SEAT_LETTER[seat]}: ").strip()
        except EOFError:
            print("\nAborted.")
            sys.exit(1)
        c = parse_card_input(text, legal)
        if c is not None:
            return c
        print("  ?  Try '1', 'SA', or 'AS'.")


def dds_pick(deal) -> Card:
    sb = solve_board(deal)
    return max(sb, key=lambda x: x[1])[0]


def play_deal(board):
    deal = board.deal
    parsed = parse_contract(board.info.get("Contract", "?"))
    if parsed is None:
        print(f"No playable contract: {board.info.get('Contract')}")
        return
    level, trump = parsed
    dealer = Player(board.dealer) if board.dealer is not None else Player.north
    declarer = derive_declarer(board.auction, dealer, trump)
    dummy = Player((int(declarer) + 2) % 4)
    opening_leader = left_of(declarer)
    tricks_needed = 6 + level

    deal.first = opening_leader
    deal.trump = trump

    user_seats = {declarer, dummy}

    print(f"\n=== {board.info.get('Event','?')} board {board.board_num} ===")
    print(f"Contract: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]}   "
          f"Dummy: {SEAT_LETTER[dummy]}   Opening leader: {SEAT_LETTER[opening_leader]}")
    print(f"You play both {SEAT_LETTER[declarer]} (declarer) and {SEAT_LETTER[dummy]} (dummy).")
    print(f"DDS plays the defenders.\n")

    ns_tricks = ew_tricks = 0

    for trick_num in range(1, 14):
        print(f"\n--- Trick {trick_num}  (NS:{ns_tricks}  EW:{ew_tricks}) ---")
        print(f"{SEAT_LETTER[declarer]} (you, declarer):")
        print(render_hand(hand_of(deal, declarer)))
        print(f"{SEAT_LETTER[dummy]} (dummy):")
        print(render_hand(hand_of(deal, dummy)))

        leader = deal.first
        plays = []
        for _ in range(4):
            seat = deal.curplayer
            if seat in user_seats:
                card = prompt_user_card(seat, deal)
            else:
                card = dds_pick(deal)
                print(f"  {SEAT_LETTER[seat]} plays {card}")
            plays.append((seat, card))
            deal.play(card)
        winner = deal.curplayer
        if winner in (Player.north, Player.south):
            ns_tricks += 1
        else:
            ew_tricks += 1
        order = ", ".join(f"{SEAT_LETTER[s]}:{c}" for s, c in plays)
        print(f"  Trick {trick_num}: led by {SEAT_LETTER[leader]} — {order}  →  won by {SEAT_LETTER[winner]}")

    declarer_tricks = ns_tricks if declarer in (Player.north, Player.south) else ew_tricks
    offset = declarer_tricks - tricks_needed
    result_str = "=" if offset == 0 else (f"+{offset}" if offset > 0 else str(offset))
    print(f"\nFinal: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]} "
          f"makes {declarer_tricks} ({result_str})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="Major_Suit_Fit")
    ap.add_argument("--board", type=int, default=0)
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

    play_deal(boards[args.board])
    return 0


if __name__ == "__main__":
    sys.exit(main())
