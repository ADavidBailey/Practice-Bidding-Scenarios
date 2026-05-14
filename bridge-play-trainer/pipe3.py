"""
Pipe 3 — Claude-graded inference after each trick.

Same play loop as pipe 2 (user is declarer + dummy, DDS plays defenders). After
each completed trick, prompt user for a free-text read on East/West, send to
Claude with full context, print graded feedback + next-trick hint.

Requires ANTHROPIC_API_KEY in the environment.

Run:
    python3 bridge-play-trainer/pipe3.py
    python3 bridge-play-trainer/pipe3.py --scenario Major_Suit_Fit --board 0
    python3 bridge-play-trainer/pipe3.py --skip-inference   # play without Claude
"""

import argparse
import json
import os
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
CLAUDE_MODEL = "claude-opus-4-7"


def left_of(p):
    return Player((int(p) + 1) % 4)


def partner_of(p):
    return Player((int(p) + 2) % 4)


def parse_contract(s):
    if not s or s in ("?", "Pass"):
        return None
    level = int(s[0])
    strain = s[1:].rstrip("X")
    m = {"S": Denom.spades, "H": Denom.hearts, "D": Denom.diamonds, "C": Denom.clubs, "N": Denom.nt, "NT": Denom.nt}
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
        seat = left_of(seat)
    winning_side = "NS" if last_bidder in (Player.north, Player.south) else "EW"
    return final[(winning_side, trump)]


def hand_of(deal, seat):
    return [deal.north, deal.east, deal.south, deal.west][int(seat)]


def hand_str(hand) -> str:
    return f"♠{''.join(r.abbr for r in hand.spades) or '-'} " \
           f"♥{''.join(r.abbr for r in hand.hearts) or '-'} " \
           f"♦{''.join(r.abbr for r in hand.diamonds) or '-'} " \
           f"♣{''.join(r.abbr for r in hand.clubs) or '-'}"


def render_hand(hand):
    return "\n".join([
        f"  ♠ {' '.join(r.abbr for r in hand.spades) or '-'}",
        f"  ♥ {' '.join(r.abbr for r in hand.hearts) or '-'}",
        f"  ♦ {' '.join(r.abbr for r in hand.diamonds) or '-'}",
        f"  ♣ {' '.join(r.abbr for r in hand.clubs) or '-'}",
    ])


def auction_str(auction, dealer) -> str:
    seat = dealer
    rows = []
    for call in auction:
        if hasattr(call, "denom"):
            if call.denom == Denom.nt:
                txt = f"{call.level}NT"
            else:
                txt = f"{call.level}{DENOM_SYM[call.denom]}"
        else:
            penalty = getattr(call, "penalty", None)
            pn = getattr(penalty, "name", None) if penalty is not None else None
            txt = {"passed": "Pass", "doubled": "X", "redoubled": "XX"}.get(pn, "Pass")
        rows.append((SEAT_LETTER[seat], txt))
        seat = left_of(seat)
    return " ".join(f"{s}:{c}" for s, c in rows)


def parse_card_input(text, legal):
    t = text.strip().upper().replace(" ", "")
    if not t:
        return None
    if t.isdigit():
        i = int(t) - 1
        if 0 <= i < len(legal):
            return legal[i]
        return None
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


def prompt_card(seat, deal):
    legal = list(deal.legal_moves())
    print(f"\n  Legal for {SEAT_LETTER[seat]}:  " + "  ".join(f"[{i+1}]{c}" for i, c in enumerate(legal)))
    while True:
        try:
            t = input(f"  Play for {SEAT_LETTER[seat]}: ")
        except EOFError:
            sys.exit(1)
        c = parse_card_input(t, legal)
        if c is not None:
            return c
        print("  ?  Try '1', 'SA', 'AS', or '♠A'.")


def dds_pick(deal):
    sb = solve_board(deal)
    return max(sb, key=lambda x: x[1])[0]


# ---------- Claude inference layer ----------

INFERENCE_SYSTEM_PROMPT = """You are a bridge instructor evaluating a student's read on hidden defender hands during a deal.

You receive: the auction, declarer's hand, dummy's hand, the cards played so far, and the student's free-text estimate of East and West's hands.

Evaluate the estimate against:
1. What's logically inferrable from the auction (failure-to-act, bid-meaning constraints)
2. What's inferrable from the lead and signal style (top-of-sequence, attitude, count)
3. What's inferrable from cards already played (suit lengths becoming known, honors located)

Return JSON only, no prose around it, matching this schema:

{
  "facets": [
    {"claim": "<student's stated claim, brief>", "verdict": "correct|partial|missed|wrong", "note": "<one sentence why>"}
  ],
  "missed_inferences": ["<important inference the student did not state>"],
  "next_trick_hint": "<one sentence on what to watch for next trick>",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}

Be concrete and bridge-literate. Reference specific cards and bids. Keep notes to one short sentence."""


def build_inference_payload(deal, board, declarer, dummy, trick_history, current_known, user_text):
    """Build the user-message content for Claude."""
    contract_str = board.info.get("Contract", "?")
    auction = auction_str(board.auction, Player(board.dealer))
    decl_hand_initial = current_known["declarer_initial"]
    dummy_hand_initial = current_known["dummy_initial"]

    play_log = []
    for trick in trick_history:
        play_log.append(
            f"Trick {trick['n']}: led by {trick['leader']} — "
            + ", ".join(f"{p['seat']}:{p['card']}" for p in trick['plays'])
            + f"  won by {trick['winner']}"
        )

    return f"""## Auction
Dealer: {SEAT_LETTER[Player(board.dealer)]}
{auction}
Final contract: {contract_str} by {SEAT_LETTER[declarer]}

## Visible hands (initial)
Declarer ({SEAT_LETTER[declarer]}): {decl_hand_initial}
Dummy ({SEAT_LETTER[dummy]}): {dummy_hand_initial}

## Play so far ({len(trick_history)} tricks completed)
{chr(10).join(play_log) if play_log else "(no tricks played yet)"}

## Student's estimate of East/West
{user_text.strip()}

Evaluate. Return JSON only."""


def call_claude(client, payload: str):
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        system=INFERENCE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": payload}],
    )
    text = "".join(block.text for block in msg.content if block.type == "text").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


VERDICT_ICON = {"correct": "✅", "partial": "⚠️", "missed": "❌", "wrong": "❌"}


def print_eval(ev):
    print(f"\n  Overall: {ev.get('overall','?').upper()}   (score {ev.get('score', 0):.2f})")
    for f in ev.get("facets", []):
        icon = VERDICT_ICON.get(f.get("verdict", ""), "•")
        print(f"  {icon} {f.get('claim','')} — {f.get('note','')}")
    for m in ev.get("missed_inferences", []):
        print(f"  ❌ MISSED: {m}")
    hint = ev.get("next_trick_hint")
    if hint:
        print(f"  🎯 Next trick: {hint}")


# ---------- Main loop ----------

def play_deal(board, skip_inference: bool):
    deal = board.deal
    parsed = parse_contract(board.info.get("Contract", "?"))
    if parsed is None:
        print("No contract.")
        return
    level, trump = parsed
    dealer = Player(board.dealer) if board.dealer is not None else Player.north
    declarer = derive_declarer(board.auction, dealer, trump)
    dummy = partner_of(declarer)
    leader = left_of(declarer)
    deal.first = leader
    deal.trump = trump
    user_seats = {declarer, dummy}
    needed = 6 + level

    declarer_initial = hand_str(hand_of(deal, declarer))
    dummy_initial = hand_str(hand_of(deal, dummy))
    known = {"declarer_initial": declarer_initial, "dummy_initial": dummy_initial}

    client = None
    if not skip_inference:
        try:
            import anthropic
            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        except ImportError:
            print("anthropic SDK missing — install with: pip3 install anthropic")
            print("Continuing without inference.")
        except Exception as e:
            print(f"Anthropic client setup failed: {e}\nContinuing without inference.")

    print(f"\n=== {board.info.get('Event','?')} board {board.board_num} ===")
    print(f"Contract: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]}   "
          f"Dummy: {SEAT_LETTER[dummy]}   Leader: {SEAT_LETTER[leader]}")
    print(f"You play {SEAT_LETTER[declarer]} (declarer) + {SEAT_LETTER[dummy]} (dummy). DDS plays defenders.\n")

    ns = ew = 0
    trick_history = []

    for trick_num in range(1, 14):
        print(f"\n----- Trick {trick_num}   (NS:{ns}  EW:{ew}) -----")
        print(f"{SEAT_LETTER[declarer]} (you):")
        print(render_hand(hand_of(deal, declarer)))
        print(f"{SEAT_LETTER[dummy]} (dummy):")
        print(render_hand(hand_of(deal, dummy)))

        tr_leader = deal.first
        plays = []
        for _ in range(4):
            seat = deal.curplayer
            if seat in user_seats:
                card = prompt_card(seat, deal)
            else:
                card = dds_pick(deal)
                print(f"  {SEAT_LETTER[seat]} plays {card}")
            plays.append({"seat": SEAT_LETTER[seat], "card": str(card)})
            deal.play(card)
        winner = deal.curplayer
        if winner in (Player.north, Player.south):
            ns += 1
        else:
            ew += 1
        trick_history.append({
            "n": trick_num,
            "leader": SEAT_LETTER[tr_leader],
            "plays": plays,
            "winner": SEAT_LETTER[winner],
        })
        print(f"  Trick {trick_num}: " + ", ".join(f"{p['seat']}:{p['card']}" for p in plays) +
              f"  → won by {SEAT_LETTER[winner]}")

        if client is not None and trick_num < 13:
            try:
                user_text = input(
                    f"\n  Your read on East & West (free text, blank to skip): "
                ).strip()
            except EOFError:
                user_text = ""
            if user_text:
                payload = build_inference_payload(
                    deal, board, declarer, dummy, trick_history, known, user_text
                )
                print("  ... evaluating ...")
                try:
                    ev = call_claude(client, payload)
                    print_eval(ev)
                except Exception as e:
                    print(f"  Claude call failed: {e}")

    decl_tricks = ns if declarer in (Player.north, Player.south) else ew
    off = decl_tricks - needed
    res = "=" if off == 0 else (f"+{off}" if off > 0 else str(off))
    print(f"\nFinal: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]} makes {decl_tricks} ({res})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="Major_Suit_Fit")
    ap.add_argument("--board", type=int, default=0)
    ap.add_argument("--skip-inference", action="store_true")
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

    if not args.skip_inference and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not set. Inference will be skipped.")
        print("Set with: export ANTHROPIC_API_KEY=sk-ant-...")
        args.skip_inference = True

    play_deal(boards[args.board], skip_inference=args.skip_inference)
    return 0


if __name__ == "__main__":
    sys.exit(main())
