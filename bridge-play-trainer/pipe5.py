"""
Pipe 5 — defender mode (and declarer mode).

  --role declarer (default)   You play declarer + dummy; DDS plays defenders.
  --role defender_e           You play East; DDS plays N, S, W.
  --role defender_w           You play West; DDS plays N, S, E.

In defender mode you see your own hand from the start, and dummy is exposed
after the opening lead — exactly like real bridge. Inference prompts ask about
declarer's and partner's hands (the two still hidden).

Run:
    python3 bridge-play-trainer/pipe5.py --role defender_e --board 0
    python3 bridge-play-trainer/pipe5.py --role defender_w --input-mode structured
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
LETTER_SEAT = {v: k for k, v in SEAT_LETTER.items()}
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


def hand_str(hand):
    return f"♠{''.join(r.abbr for r in hand.spades) or '-'} " \
           f"♥{''.join(r.abbr for r in hand.hearts) or '-'} " \
           f"♦{''.join(r.abbr for r in hand.diamonds) or '-'} " \
           f"♣{''.join(r.abbr for r in hand.clubs) or '-'}"


def hand_lengths(hand):
    return {"S": sum(1 for _ in hand.spades), "H": sum(1 for _ in hand.hearts),
            "D": sum(1 for _ in hand.diamonds), "C": sum(1 for _ in hand.clubs)}


def hand_hcp(hand):
    return sum(HONOR_HCP.get(r, 0)
               for it in (hand.spades, hand.hearts, hand.diamonds, hand.clubs) for r in it)


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
        return legal[i] if 0 <= i < len(legal) else None
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


# ---------- structured prompt ----------

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
        print(f"  ?  Whole number between {lo} and {hi}.")


def prompt_structured(target_seats, target_labels, remaining_in_suits, remaining_hcp):
    """target_seats: list of 2 seat letters to ask about, e.g. ['Declarer (S)', 'Partner (E)']."""
    print(f"\n  Hidden cards still out — by suit:  "
          f"♠{remaining_in_suits['S']}  ♥{remaining_in_suits['H']}  "
          f"♦{remaining_in_suits['D']}  ♣{remaining_in_suits['C']}  "
          f"(HCP still unseen: {remaining_hcp})")
    print("  Press Enter on any field to skip and give free text instead.\n")

    est = {}
    for key, label in zip(target_seats, target_labels):
        print(f"  -- Your read of {label} --")
        lengths = {}
        for suit in ("S", "H", "D", "C"):
            sym = {"S":"♠","H":"♥","D":"♦","C":"♣"}[suit]
            n = prompt_int(f"    {sym} length: ", 0, 13)
            if n is None:
                return None
            lengths[suit] = n
        if sum(lengths.values()) != 13:
            print(f"  ⚠ lengths sum to {sum(lengths.values())}, not 13. (Claude will note.)")
        hcp = prompt_int(f"    HCP estimate: ", 0, 40)
        if hcp is None:
            return None
        est[key] = {"lengths": lengths, "hcp": hcp}

    a, b = target_seats
    for suit in ("S", "H", "D", "C"):
        total = est[a]["lengths"][suit] + est[b]["lengths"][suit]
        if total != remaining_in_suits[suit]:
            sym = {"S":"♠","H":"♥","D":"♦","C":"♣"}[suit]
            print(f"  ⚠ {sym}: your {a}+{b} total = {total}, but {remaining_in_suits[suit]} are unseen.")
    if est[a]["hcp"] + est[b]["hcp"] != remaining_hcp:
        diff = est[a]["hcp"] + est[b]["hcp"] - remaining_hcp
        sign = "+" if diff > 0 else ""
        print(f"  ⚠ HCP: total is {sign}{diff} off the {remaining_hcp} unseen.")
    return est


# ---------- Claude grading ----------

FREE_SYSTEM = """You are a bridge instructor grading a student's free-text read on the hidden hands during a deal.

You receive: the auction, the hands visible to the student, the cards played so far, the ACTUAL hidden hands (ground truth — known only to you), and the student's prose estimate.

Grade the student's stated claims against ground truth AND against what was inferrable from the visible evidence.

Return JSON only:
{
  "facets": [{"claim": "...", "verdict": "correct|partial|missed|wrong", "note": "<one sentence>"}],
  "missed_inferences": ["..."],
  "next_trick_hint": "...",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}"""

STRUCTURED_SYSTEM = """You are a bridge instructor grading a student's structured read on hidden hands.

You receive: the auction, visible hands, play history, ACTUAL hidden hands (ground truth), and the student's per-hand suit-lengths + HCP estimates.

For EACH hidden hand, grade each suit-length and HCP separately:
- length exact = correct, ±1 = partial, ±2+ = wrong
- HCP within ±1 = correct, within ±3 = partial, ±4+ = wrong

Return JSON only:
{
  "facets": [{"claim": "<who> <suit/HCP> = <student> (actual: <truth>)", "verdict": "...", "note": "..."}],
  "reasoning_notes": ["<short observations on WHY the actual hand was inferrable>"],
  "next_trick_hint": "...",
  "overall": "excellent|good|partial|poor",
  "score": <0.0..1.0>
}"""


def build_free_payload(board, role_desc, visible_block, hidden_block, trick_history, user_text):
    return f"""## Auction
Dealer: {SEAT_LETTER[Player(board.dealer)]}
{auction_str(board.auction, Player(board.dealer))}
Final contract: {board.info.get('Contract','?')}

## Role
{role_desc}

## Visible to student
{visible_block}

## Hidden (ground truth — NOT shown to student)
{hidden_block}

## Play so far ({len(trick_history)} tricks)
{chr(10).join(f"Trick {t['n']}: led by {t['leader']} — " + ', '.join(f"{p['seat']}:{p['card']}" for p in t['plays']) + f"  won by {t['winner']}" for t in trick_history) or "(none)"}

## Student's prose estimate
{user_text.strip()}

Return JSON only."""


def build_structured_payload(board, role_desc, visible_block, hidden_block,
                             trick_history, estimate, actual_lengths, actual_hcp):
    student_lines = []
    for k, v in estimate.items():
        student_lines.append(
            f"{k}: ♠{v['lengths']['S']} ♥{v['lengths']['H']} ♦{v['lengths']['D']} ♣{v['lengths']['C']}   HCP={v['hcp']}"
        )
    actual_lines = []
    for k in estimate.keys():
        a = actual_lengths[k]
        actual_lines.append(
            f"{k}: ♠{a['S']} ♥{a['H']} ♦{a['D']} ♣{a['C']}   HCP={actual_hcp[k]}"
        )
    return f"""## Auction
Dealer: {SEAT_LETTER[Player(board.dealer)]}
{auction_str(board.auction, Player(board.dealer))}
Final contract: {board.info.get('Contract','?')}

## Role
{role_desc}

## Visible to student
{visible_block}

## Ground truth for the hidden hands (NOT shown to student)
{chr(10).join(actual_lines)}
{hidden_block}

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

def resolve_role(role, declarer, dummy):
    """Return (user_seats, hidden_seats, role_desc, user_letter)."""
    if role == "declarer":
        defenders = [s for s in (Player.north, Player.east, Player.south, Player.west) if s not in (declarer, dummy)]
        return (
            {declarer, dummy},
            list(defenders),
            f"Student is declarer ({SEAT_LETTER[declarer]}). Dummy is {SEAT_LETTER[dummy]}.",
            None,
        )
    me = LETTER_SEAT[role[-1].upper()]
    if me in (declarer, dummy):
        return None
    partner = partner_of(me)
    return (
        {me},
        [declarer, partner],
        f"Student is defender ({SEAT_LETTER[me]}). Partner is {SEAT_LETTER[partner]}. "
        f"Declarer is {SEAT_LETTER[declarer]}, dummy is {SEAT_LETTER[dummy]}.",
        SEAT_LETTER[me],
    )


def play_deal(board, role: str, input_mode: str, skip_inference: bool):
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

    resolved = resolve_role(role, declarer, dummy)
    if resolved is None:
        me = role[-1].upper()
        print(f"This board has {SEAT_LETTER[declarer]} declaring — {me} can't defend it here.")
        print("Try a different --board.")
        return
    user_seats, hidden_seats, role_desc, user_letter = resolved
    needed = 6 + level

    decl_init = hand_str(hand_of(deal, declarer))
    dummy_init = hand_str(hand_of(deal, dummy))

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
    print(f"Contract: {level}{DENOM_SYM[trump]} by {SEAT_LETTER[declarer]}   Leader: {SEAT_LETTER[leader]}")
    print(f"{role_desc}")
    print(f"Inference mode: {input_mode}")

    ns = ew = 0
    trick_history = []
    cards_played = 0

    for trick_num in range(1, 14):
        dummy_visible_now = (role == "declarer") or (cards_played >= 1)

        print(f"\n----- Trick {trick_num}   (NS:{ns}  EW:{ew}) -----")
        if role == "declarer":
            print(f"{SEAT_LETTER[declarer]} (you):"); print(render_hand(hand_of(deal, declarer)))
            print(f"{SEAT_LETTER[dummy]} (dummy):"); print(render_hand(hand_of(deal, dummy)))
        else:
            me = next(iter(user_seats))
            print(f"{SEAT_LETTER[me]} (you):"); print(render_hand(hand_of(deal, me)))
            if dummy_visible_now:
                print(f"{SEAT_LETTER[dummy]} (dummy):"); print(render_hand(hand_of(deal, dummy)))
            else:
                print(f"{SEAT_LETTER[dummy]} (dummy): face-down until after opening lead")

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
            cards_played += 1
        winner = deal.curplayer
        if winner in (Player.north, Player.south): ns += 1
        else: ew += 1
        trick_history.append({"n": trick_num, "leader": SEAT_LETTER[tr_leader], "plays": plays, "winner": SEAT_LETTER[winner]})
        print(f"  Trick {trick_num}: " + ", ".join(f"{p['seat']}:{p['card']}" for p in plays) + f"  → won by {SEAT_LETTER[winner]}")

        if client is None or trick_num >= 13:
            continue

        hidden_letters = [SEAT_LETTER[s] for s in hidden_seats]
        hidden_labels = []
        for s in hidden_seats:
            if s == declarer:
                hidden_labels.append(f"declarer ({SEAT_LETTER[s]})")
            elif role != "declarer" and s == partner_of(next(iter(user_seats))):
                hidden_labels.append(f"partner ({SEAT_LETTER[s]})")
            else:
                hidden_labels.append(f"{SEAT_LETTER[s]}")

        full_initial = build_initial_hands(board)
        actual_lengths = {SEAT_LETTER[s]: hand_lengths(full_initial[s]) for s in hidden_seats}
        actual_hcp = {SEAT_LETTER[s]: hand_hcp(full_initial[s]) for s in hidden_seats}

        visible_block_lines = []
        if role == "declarer":
            visible_block_lines.append(f"Declarer ({SEAT_LETTER[declarer]}): {decl_init}")
            visible_block_lines.append(f"Dummy ({SEAT_LETTER[dummy]}): {dummy_init}")
        else:
            me = next(iter(user_seats))
            visible_block_lines.append(f"Defender ({SEAT_LETTER[me]}): {hand_str(full_initial[me])}")
            visible_block_lines.append(f"Dummy ({SEAT_LETTER[dummy]}): {dummy_init}")
        visible_block = "\n".join(visible_block_lines)

        hidden_block_lines = [f"{SEAT_LETTER[s]}: {hand_str(full_initial[s])}" for s in hidden_seats]
        hidden_block = "\n".join(hidden_block_lines)

        use_structured = (
            input_mode == "structured" or
            (input_mode == "auto" and trick_num >= STRUCTURED_FROM_TRICK)
        )

        if use_structured:
            remaining_suits = {k: 0 for k in "SHDC"}
            for s in hidden_seats:
                live = hand_lengths(hand_of(deal, s))
                for k in "SHDC":
                    remaining_suits[k] += live[k]
            remaining_hcp = sum(hand_hcp(hand_of(deal, s)) for s in hidden_seats)

            estimate = prompt_structured(hidden_letters, hidden_labels, remaining_suits, remaining_hcp)
            if estimate is None:
                try:
                    user_text = input("  Free text instead (blank to skip): ").strip()
                except EOFError:
                    user_text = ""
                if not user_text:
                    continue
                payload = build_free_payload(board, role_desc, visible_block, hidden_block, trick_history, user_text)
                system = FREE_SYSTEM
            else:
                payload = build_structured_payload(board, role_desc, visible_block, hidden_block,
                                                   trick_history, estimate, actual_lengths, actual_hcp)
                system = STRUCTURED_SYSTEM
        else:
            prompt_label = "  Your read on " + " and ".join(hidden_labels) + " (free text, blank to skip): "
            try:
                user_text = input("\n" + prompt_label).strip()
            except EOFError:
                user_text = ""
            if not user_text:
                continue
            payload = build_free_payload(board, role_desc, visible_block, hidden_block, trick_history, user_text)
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


def build_initial_hands(board):
    """Return a fresh dict {Player: Hand} from a fresh re-parse — used for ground-truth payloads."""
    # We can't re-parse mid-deal cheaply, so reconstruct from board's stored deal at trick 0.
    # The board.deal we hold has already been mutated by play(). Trick the parser:
    # The PBN library exposes the deal at trick 0 via the original board attribute we never mutate? No — we mutated.
    # Cheaper: copy original hands at the start of play_deal and pass them in. We do that for E/W via east_hand_init/west_hand_init,
    # but N/S also mutate. Use the board's underlying string representation captured at load.
    # Simplest correct approach: keep a snapshot. We pass the board in here, so just stash on board.
    snap = getattr(board, "_initial_hands_snapshot", None)
    if snap is None:
        raise RuntimeError("initial hands snapshot missing")
    return snap


def snapshot_initial_hands(board):
    d = board.deal
    board._initial_hands_snapshot = {
        Player.north: d.north.copy(),
        Player.east:  d.east.copy(),
        Player.south: d.south.copy(),
        Player.west:  d.west.copy(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="Major_Suit_Fit")
    ap.add_argument("--board", type=int, default=0)
    ap.add_argument("--role", choices=["declarer", "defender_e", "defender_w"], default="declarer")
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
        args.skip_inference = True

    board = boards[args.board]
    snapshot_initial_hands(board)
    play_deal(board, role=args.role, input_mode=args.input_mode, skip_inference=args.skip_inference)
    return 0


if __name__ == "__main__":
    sys.exit(main())
