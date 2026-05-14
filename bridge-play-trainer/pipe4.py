"""
Pipe 4 — free-text early, structured later.

Same play loop as pipe 3 (you play declarer + dummy, DDS plays defenders, Claude
grades). New: at trick 4 the inference prompt switches from prose to a
structured form (4 suit-lengths + HCP per defender). Pipe 4 also feeds Claude
the actual East/West hands so grading is against ground truth.

Run:
    python3 bridge-play-trainer/pipe4.py
    python3 bridge-play-trainer/pipe4.py --input-mode auto       # default: text 1-3, structured 4+
    python3 bridge-play-trainer/pipe4.py --input-mode free       # always free-text
    python3 bridge-play-trainer/pipe4.py --input-mode structured # always structured
    python3 bridge-play-trainer/pipe4.py --skip-inference        # no Claude
"""

import argparse
import json
import os
import sys
from pathlib import Path

from endplay.types import Player, Denom, Rank
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
HONOR_HCP = {Rank.RA: 4, Rank.RK: 3, Rank.RQ: 2, Rank.RJ: 1}
CLAUDE_MODEL = "claude-opus-4-7"
STRUCTURED_FROM_TRICK = 4


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


def hand_lengths(hand):
    return {
        "S": sum(1 for _ in hand.spades),
        "H": sum(1 for _ in hand.hearts),
        "D": sum(1 for _ in hand.diamonds),
        "C": sum(1 for _ in hand.clubs),
    }


def hand_hcp(hand):
    total = 0
    for suit_iter in (hand.spades, hand.hearts, hand.diamonds, hand.clubs):
        for r in suit_iter:
            total += HONOR_HCP.get(r, 0)
    return total


def render_hand(hand):
    return "\n".join([
        f"  ♠ {' '.join(r.abbr for r in hand.spades) or '-'}",
        f"  ♥ {' '.join(r.abbr for r in hand.hearts) or '-'}",
        f"  ♦ {' '.join(r.abbr for r in hand.diamonds) or '-'}",
        f"  ♣ {' '.join(r.abbr for r in hand.clubs) or '-'}",
    ])


def auction_str(auction, dealer):
    seat = dealer
    rows = []
    for call in auction:
        if hasattr(call, "denom"):
            txt = f"{call.level}NT" if call.denom == Denom.nt else f"{call.level}{DENOM_SYM[call.denom]}"
        else:
            penalty = getattr(call, "penalty", None)
            pn = getattr(penalty, "name", None) if penalty is not None else None
            txt = {"passed": "Pass", "doubled": "X", "redoubled": "XX"}.get(pn, "Pass")
        rows.append((SEAT_LETTER[seat], txt))
        seat = left_of(seat)
    return " ".join(f"{s}:{c}" for s, c in rows)


# ---------- card input ----------

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


# ---------- structured inference input ----------

def prompt_int(label, lo=0, hi=13):
    while True:
        try:
            t = input(label).strip()
        except EOFError:
            sys.exit(1)
        if not t:
            return None
        try:
            n = int(t)
            if lo <= n <= hi:
                return n
        except ValueError:
            pass
        print(f"  ?  Enter a whole number between {lo} and {hi}.")


def prompt_structured(remaining_in_suits, remaining_hcp):
    """Ask user for ♠ ♥ ♦ ♣ lengths + HCP for East and West. Validates as it goes."""
    print(f"\n  Hidden cards still out — by suit:  "
          f"♠{remaining_in_suits['S']}  ♥{remaining_in_suits['H']}  "
          f"♦{remaining_in_suits['D']}  ♣{remaining_in_suits['C']}  "
          f"(HCP still unseen: {remaining_hcp})")
    print("  Press Enter on any field to skip the structured form and give free text instead.\n")

    est = {}
    for who in ("W", "E"):
        print(f"  -- Your read of {who}'s hand --")
        lengths = {}
        for suit in ("S", "H", "D", "C"):
            sym = {"S":"♠","H":"♥","D":"♦","C":"♣"}[suit]
            n = prompt_int(f"    {sym} length: ", 0, 13)
            if n is None:
                return None
            lengths[suit] = n
        if sum(lengths.values()) != 13:
            print(f"  ⚠ {who} lengths sum to {sum(lengths.values())}, not 13.  "
                  "(That's OK — Claude will note the inconsistency.)")
        hcp = prompt_int(f"    HCP estimate: ", 0, 40)
        if hcp is None:
            return None
        est[who] = {"lengths": lengths, "hcp": hcp}

    for suit in ("S", "H", "D", "C"):
        total = est["W"]["lengths"][suit] + est["E"]["lengths"][suit]
        if total != remaining_in_suits[suit]:
            sym = {"S":"♠","H":"♥","D":"♦","C":"♣"}[suit]
            print(f"  ⚠ {sym}: your W+E total = {total}, but {remaining_in_suits[suit]} are unseen.  "
                  "(Claude will mention.)")
    if est["W"]["hcp"] + est["E"]["hcp"] != remaining_hcp:
        diff = est["W"]["hcp"] + est["E"]["hcp"] - remaining_hcp
        sign = "+" if diff > 0 else ""
        print(f"  ⚠ HCP: your W+E total is {sign}{diff} off the {remaining_hcp} unseen.  "
              "(Claude will mention.)")
    return est


# ---------- Claude grading ----------

FREE_SYSTEM = """You are a bridge instructor evaluating a student's free-text read on the hidden defender hands during a deal.

You receive: the auction, declarer's hand, dummy's hand, the cards played so far, the ACTUAL East and West hands (ground truth — known only to you, not the student), and the student's prose estimate.

Grade the student's stated claims against ground truth AND against what was inferrable from the visible evidence. Be concrete.

Return JSON only:
{
  "facets": [
    {"claim": "<student's claim, brief>", "verdict": "correct|partial|missed|wrong", "note": "<one sentence>"}
  ],
  "missed_inferences": ["<important inference the student didn't state>"],
  "next_trick_hint": "<one sentence>",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}"""

STRUCTURED_SYSTEM = """You are a bridge instructor grading a student's structured read on hidden defender hands.

You receive: the auction, declarer's and dummy's hands, the cards played so far, the ACTUAL East and West hands (ground truth — known only to you), and the student's numeric estimate of each defender's suit-lengths and HCP.

For EACH defender, grade each suit-length and HCP separately. Use this rubric:
- length exact = correct, ±1 = partial, ±2+ = wrong
- HCP within ±1 = correct, within ±3 = partial, ±4+ = wrong
- Honor placement (if student named specific honors): correct placement = correct; wrong defender = wrong

Return JSON only:
{
  "facets": [
    {"claim": "W ♠ length = 4 (actual: 5)", "verdict": "partial", "note": "off by one"},
    ... (one row per length + one per HCP)
  ],
  "reasoning_notes": ["<short observations on WHY the actual hand was inferrable — e.g., 'pass denies 12+ HCP', 'KQJ lead reveals 3+ hearts'>"],
  "next_trick_hint": "<one sentence>",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}"""


def build_free_payload(board, declarer, dummy, trick_history, decl_init, dummy_init, east_hand, west_hand, user_text):
    return f"""## Auction
Dealer: {SEAT_LETTER[Player(board.dealer)]}
{auction_str(board.auction, Player(board.dealer))}
Final contract: {board.info.get('Contract','?')} by {SEAT_LETTER[declarer]}

## Visible to student (initial)
Declarer ({SEAT_LETTER[declarer]}): {decl_init}
Dummy ({SEAT_LETTER[dummy]}): {dummy_init}

## Ground truth (NOT shown to student — grade against this)
East: {hand_str(east_hand)}
West: {hand_str(west_hand)}

## Play so far ({len(trick_history)} tricks)
{chr(10).join(f"Trick {t['n']}: led by {t['leader']} — " + ', '.join(f"{p['seat']}:{p['card']}" for p in t['plays']) + f"  won by {t['winner']}" for t in trick_history) or "(none)"}

## Student's prose estimate
{user_text.strip()}

Return JSON only."""


def build_structured_payload(board, declarer, dummy, trick_history, decl_init, dummy_init,
                             east_hand, west_hand, estimate, actual_lengths, actual_hcp):
    student_lines = []
    for who in ("W", "E"):
        e = estimate[who]
        student_lines.append(
            f"{who}: ♠{e['lengths']['S']} ♥{e['lengths']['H']} ♦{e['lengths']['D']} ♣{e['lengths']['C']}   HCP={e['hcp']}"
        )
    actual_lines = []
    for who, hand in (("W", west_hand), ("E", east_hand)):
        a = actual_lengths[who]
        actual_lines.append(
            f"{who}: ♠{a['S']} ♥{a['H']} ♦{a['D']} ♣{a['C']}   HCP={actual_hcp[who]}   ({hand_str(hand)})"
        )

    return f"""## Auction
Dealer: {SEAT_LETTER[Player(board.dealer)]}
{auction_str(board.auction, Player(board.dealer))}
Final contract: {board.info.get('Contract','?')} by {SEAT_LETTER[declarer]}

## Visible to student (initial)
Declarer ({SEAT_LETTER[declarer]}): {decl_init}
Dummy ({SEAT_LETTER[dummy]}): {dummy_init}

## Ground truth (NOT shown to student)
{chr(10).join(actual_lines)}

## Play so far ({len(trick_history)} tricks)
{chr(10).join(f"Trick {t['n']}: led by {t['leader']} — " + ', '.join(f"{p['seat']}:{p['card']}" for p in t['plays']) + f"  won by {t['winner']}" for t in trick_history) or "(none)"}

## Student's structured estimate
{chr(10).join(student_lines)}

Grade each length and HCP separately. Return JSON only."""


def call_claude(client, system_prompt, payload):
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": payload}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


VERDICT_ICON = {"correct": "✅", "partial": "⚠️", "missed": "❌", "wrong": "❌"}


def print_eval(ev):
    print(f"\n  Overall: {str(ev.get('overall','?')).upper()}   (score {ev.get('score', 0):.2f})")
    for f in ev.get("facets", []):
        icon = VERDICT_ICON.get(f.get("verdict",""), "•")
        print(f"  {icon} {f.get('claim','')} — {f.get('note','')}")
    for r in ev.get("reasoning_notes", []):
        print(f"  💡 {r}")
    for m in ev.get("missed_inferences", []):
        print(f"  ❌ MISSED: {m}")
    hint = ev.get("next_trick_hint")
    if hint:
        print(f"  🎯 Next trick: {hint}")


# ---------- main loop ----------

def play_deal(board, input_mode: str, skip_inference: bool):
    deal = board.deal
    parsed = parse_contract(board.info.get("Contract", "?"))
    if parsed is None:
        print("No contract."); return
    level, trump = parsed
    dealer = Player(board.dealer) if board.dealer is not None else Player.north
    declarer = derive_declarer(board.auction, dealer, trump)
    dummy = partner_of(declarer)
    leader = left_of(declarer)
    deal.first = leader
    deal.trump = trump
    user_seats = {declarer, dummy}
    needed = 6 + level

    east_hand = deal.east.copy()
    west_hand = deal.west.copy()
    decl_init = hand_str(hand_of(deal, declarer))
    dummy_init = hand_str(hand_of(deal, dummy))
    actual_lengths = {"E": hand_lengths(east_hand), "W": hand_lengths(west_hand)}
    actual_hcp = {"E": hand_hcp(east_hand), "W": hand_hcp(west_hand)}

    client = None
    if not skip_inference:
        try:
            import anthropic
            client = anthropic.Anthropic()
        except ImportError:
            print("anthropic SDK missing — pip3 install anthropic"); print("Skipping grading.")
        except Exception as e:
            print(f"Anthropic setup failed: {e}\nSkipping grading.")

    print(f"\n=== {board.info.get('Event','?')} board {board.board_num} ===")
    print(f"Contract: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]}   "
          f"Dummy: {SEAT_LETTER[dummy]}   Leader: {SEAT_LETTER[leader]}")
    print(f"You play {SEAT_LETTER[declarer]} + {SEAT_LETTER[dummy]}. DDS plays defenders.")
    print(f"Inference mode: {input_mode}")

    ns = ew = 0
    trick_history = []

    for trick_num in range(1, 14):
        print(f"\n----- Trick {trick_num}   (NS:{ns}  EW:{ew}) -----")
        print(f"{SEAT_LETTER[declarer]} (you):"); print(render_hand(hand_of(deal, declarer)))
        print(f"{SEAT_LETTER[dummy]} (dummy):"); print(render_hand(hand_of(deal, dummy)))

        tr_leader = deal.first
        plays = []
        for _ in range(4):
            seat = deal.curplayer
            if seat in user_seats:
                card = prompt_card(seat, deal)
            else:
                card = dds_pick(deal); print(f"  {SEAT_LETTER[seat]} plays {card}")
            plays.append({"seat": SEAT_LETTER[seat], "card": str(card)})
            deal.play(card)
        winner = deal.curplayer
        if winner in (Player.north, Player.south): ns += 1
        else: ew += 1
        trick_history.append({"n": trick_num, "leader": SEAT_LETTER[tr_leader], "plays": plays, "winner": SEAT_LETTER[winner]})
        print(f"  Trick {trick_num}: " + ", ".join(f"{p['seat']}:{p['card']}" for p in plays) + f"  → won by {SEAT_LETTER[winner]}")

        if client is None or trick_num >= 13:
            continue

        use_structured = (
            input_mode == "structured" or
            (input_mode == "auto" and trick_num >= STRUCTURED_FROM_TRICK)
        )

        if use_structured:
            remaining_suits = {}
            for suit_key, denom in (("S", Denom.spades), ("H", Denom.hearts), ("D", Denom.diamonds), ("C", Denom.clubs)):
                played_in_suit = sum(
                    1 for t in trick_history for p in t['plays']
                    if (p['card'][0] in DENOM_SYM.values() and SUIT_FROM_CHAR.get(p['card'][0]) == denom)
                    or (p['card'][0].upper() in SUIT_FROM_CHAR and SUIT_FROM_CHAR.get(p['card'][0].upper()) == denom)
                )
                decl_visible = hand_lengths(hand_of(deal, declarer))[suit_key]
                dummy_visible = hand_lengths(hand_of(deal, dummy))[suit_key]
                # original count = 13 in each suit; remaining unseen = 13 - cards played from unseen hands - visible cards left
                # Simpler: actual E+W length remaining = sum of current east/west holdings
                remaining_suits[suit_key] = hand_lengths(deal.east)[suit_key] + hand_lengths(deal.west)[suit_key]
            remaining_hcp_total = hand_hcp(deal.east) + hand_hcp(deal.west)

            estimate = prompt_structured(remaining_suits, remaining_hcp_total)
            if estimate is None:
                try:
                    user_text = input("  Free text instead (blank to skip): ").strip()
                except EOFError:
                    user_text = ""
                if not user_text:
                    continue
                payload = build_free_payload(board, declarer, dummy, trick_history, decl_init, dummy_init,
                                             east_hand, west_hand, user_text)
                system = FREE_SYSTEM
            else:
                payload = build_structured_payload(board, declarer, dummy, trick_history, decl_init, dummy_init,
                                                   east_hand, west_hand, estimate, actual_lengths, actual_hcp)
                system = STRUCTURED_SYSTEM
        else:
            try:
                user_text = input("\n  Your read on East & West (free text, blank to skip): ").strip()
            except EOFError:
                user_text = ""
            if not user_text:
                continue
            payload = build_free_payload(board, declarer, dummy, trick_history, decl_init, dummy_init,
                                         east_hand, west_hand, user_text)
            system = FREE_SYSTEM

        print("  ... evaluating ...")
        try:
            ev = call_claude(client, system, payload)
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
    ap.add_argument("--input-mode", choices=["auto", "free", "structured"], default="auto")
    ap.add_argument("--skip-inference", action="store_true")
    args = ap.parse_args()

    path = BBA_DIR / f"{args.scenario}.pbn"
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr); return 2
    with open(path) as f:
        boards = list(pbn.load(f))
    if args.board >= len(boards):
        print(f"ERROR: board {args.board} out of range (0..{len(boards)-1})", file=sys.stderr); return 2

    if not args.skip_inference and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Note: ANTHROPIC_API_KEY not set. Skipping Claude grading.")
        print("Set with: export ANTHROPIC_API_KEY=sk-ant-...")
        args.skip_inference = True

    play_deal(boards[args.board], input_mode=args.input_mode, skip_inference=args.skip_inference)
    return 0


if __name__ == "__main__":
    sys.exit(main())
