"""
Bridge Play Trainer — FastAPI backend.

Start with:
    uvicorn bridge-play-trainer.server:app --reload --port 8765

Then open http://localhost:8765/ in your browser.

Declarer mode only for the MVP. Defender mode + Claude grading come next.
"""

import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from endplay.types import Player, Denom, Rank, Deal
from endplay.dds import solve_board
from endplay.parsers import pbn

REPO_ROOT = Path(__file__).resolve().parent.parent
BBA_DIR = REPO_ROOT / "bba"
STATIC_DIR = Path(__file__).resolve().parent / "static"

SEAT_LETTER = {Player.north: "N", Player.east: "E", Player.south: "S", Player.west: "W"}
LETTER_SEAT = {v: k for k, v in SEAT_LETTER.items()}
DENOM_LETTER = {Denom.spades: "S", Denom.hearts: "H", Denom.diamonds: "D", Denom.clubs: "C", Denom.nt: "NT"}
DENOM_SYM = {Denom.spades: "♠", Denom.hearts: "♥", Denom.diamonds: "♦", Denom.clubs: "♣", Denom.nt: "NT"}
SUIT_FROM_CHAR = {"S": Denom.spades, "H": Denom.hearts, "D": Denom.diamonds, "C": Denom.clubs}
RANK_FROM_CHAR = {"A": Rank.RA, "K": Rank.RK, "Q": Rank.RQ, "J": Rank.RJ, "T": Rank.RT,
                  "9": Rank.R9, "8": Rank.R8, "7": Rank.R7, "6": Rank.R6, "5": Rank.R5,
                  "4": Rank.R4, "3": Rank.R3, "2": Rank.R2}
HONOR_HCP = {Rank.RA: 4, Rank.RK: 3, Rank.RQ: 2, Rank.RJ: 1}


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


def hand_to_dict(hand):
    return {
        "S": [r.abbr for r in hand.spades],
        "H": [r.abbr for r in hand.hearts],
        "D": [r.abbr for r in hand.diamonds],
        "C": [r.abbr for r in hand.clubs],
    }


def hand_hcp(hand):
    return sum(HONOR_HCP.get(r, 0)
               for it in (hand.spades, hand.hearts, hand.diamonds, hand.clubs) for r in it)


def auction_dict(auction, dealer):
    seat = dealer
    rows = []
    for call in auction:
        if hasattr(call, "denom"):
            txt = f"{call.level}NT" if call.denom == Denom.nt else f"{call.level}{DENOM_SYM[call.denom]}"
            ann = getattr(call, "announcement", None)
        else:
            penalty = getattr(call, "penalty", None)
            pn = getattr(penalty, "name", None) if penalty is not None else None
            txt = {"passed": "Pass", "doubled": "X", "redoubled": "XX"}.get(pn, "Pass")
            ann = None
        rows.append({"seat": SEAT_LETTER[seat], "call": txt, "annotation": ann})
        seat = left_of(seat)
    return rows


def card_to_str(card):
    return f"{DENOM_LETTER[card.suit]}{card.rank.abbr}"


def card_to_display(card):
    return f"{DENOM_SYM[card.suit]}{card.rank.abbr}"


def dds_pick(deal):
    sb = solve_board(deal)
    return max(sb, key=lambda x: x[1])[0]


# ---------- session state ----------

class Session:
    def __init__(self, board, role: str):
        self.board = board
        self.deal = board.deal
        parsed = parse_contract(board.info.get("Contract", "?"))
        self.level, self.trump = parsed
        self.dealer = Player(board.dealer) if board.dealer is not None else Player.north
        self.declarer = derive_declarer(board.auction, self.dealer, self.trump)
        self.dummy = partner_of(self.declarer)
        self.leader = left_of(self.declarer)
        self.deal.first = self.leader
        self.deal.trump = self.trump
        self.role = role
        self.tricks_needed = 6 + self.level

        if role == "declarer":
            self.user_seats = {self.declarer, self.dummy}
        elif role == "defender_e":
            self.user_seats = {Player.east}
        elif role == "defender_w":
            self.user_seats = {Player.west}
        else:
            raise ValueError(f"unknown role {role}")

        self.initial_hands = {
            Player.north: self.deal.north.copy(),
            Player.east:  self.deal.east.copy(),
            Player.south: self.deal.south.copy(),
            Player.west:  self.deal.west.copy(),
        }
        self.trick_history = []
        self.current_trick_plays = []
        self.cards_played_count = 0
        self.ns_tricks = 0
        self.ew_tricks = 0
        self.complete = False
        # Full log of cards played, in chronological order. We rebuild deal
        # state from scratch when undoing, since endplay's unplay() can't
        # cross trick boundaries.
        self.move_log: list = []
        # Each /play (and /claim) records the cards_played_count BEFORE its
        # action. Undo pops the top and replays from move_log up to that count.
        self.undo_stack = []

    def visible_hands(self):
        if self.role == "declarer":
            return {self.declarer, self.dummy}
        me = next(iter(self.user_seats))
        if self.cards_played_count >= 1:
            return {me, self.dummy}
        return {me}

    def cards_played_by_seat(self):
        by_seat = {p: [] for p in (Player.north, Player.east, Player.south, Player.west)}
        for t in self.trick_history:
            for p in t["plays"]:
                by_seat[LETTER_SEAT[p["seat"]]].append(p["card"])
        for p in self.current_trick_plays:
            by_seat[LETTER_SEAT[p["seat"]]].append(p["card"])
        return {SEAT_LETTER[p]: cards for p, cards in by_seat.items()}

    def state(self):
        visible = self.visible_hands()
        hands = {}
        for p in (Player.north, Player.east, Player.south, Player.west):
            if p in visible:
                hands[SEAT_LETTER[p]] = hand_to_dict(hand_of(self.deal, p))
            else:
                hands[SEAT_LETTER[p]] = None

        current_to_play = self.deal.curplayer if not self.complete else None
        legal = []
        if current_to_play is not None and current_to_play in self.user_seats and not self.complete:
            legal = [{"suit": DENOM_LETTER[c.suit], "rank": c.rank.abbr, "display": card_to_display(c)}
                     for c in self.deal.legal_moves()]

        st = {
            "level": self.level,
            "strain": DENOM_LETTER[self.trump],
            "strain_symbol": DENOM_SYM[self.trump],
            "declarer": SEAT_LETTER[self.declarer],
            "dummy": SEAT_LETTER[self.dummy],
            "leader": SEAT_LETTER[self.leader],
            "dealer": SEAT_LETTER[self.dealer],
            "role": self.role,
            "trick_number": 13 if self.complete else len(self.trick_history) + 1,
            "tricks_taken": {"NS": self.ns_tricks, "EW": self.ew_tricks},
            "tricks_needed": self.tricks_needed,
            "hands": hands,
            "cards_played_by_seat": self.cards_played_by_seat(),
            "current_trick": [
                {"seat": p["seat"], "card": p["card"]}
                for p in self.current_trick_plays
            ],
            "trick_history": self.trick_history,
            "to_play": SEAT_LETTER[current_to_play] if current_to_play is not None else None,
            "user_to_play": current_to_play in self.user_seats if current_to_play is not None else False,
            "legal_moves": legal,
            "complete": self.complete,
            "can_undo": len(self.undo_stack) > 0,
        }
        if self.complete:
            decl_tricks = self.ns_tricks if self.declarer in (Player.north, Player.south) else self.ew_tricks
            off = decl_tricks - self.tricks_needed
            st["result"] = {
                "declarer_tricks": decl_tricks,
                "result_offset": off,
                "result_str": "=" if off == 0 else (f"+{off}" if off > 0 else str(off)),
                "all_hands": {SEAT_LETTER[p]: hand_to_dict(self.initial_hands[p])
                              for p in self.initial_hands},
                "all_hcp": {SEAT_LETTER[p]: hand_hcp(self.initial_hands[p])
                            for p in self.initial_hands},
            }
        st["auction"] = auction_dict(self.board.auction, self.dealer)
        st["contract_str"] = f"{self.level}{DENOM_SYM[self.trump]} by {SEAT_LETTER[self.declarer]}"
        st["board_num"] = self.board.board_num
        st["scenario"] = self.board.info.get("Event", "?")
        return st

    def play_user_card(self, suit_letter: str, rank_letter: str):
        if self.complete:
            raise HTTPException(400, "deal complete")
        if self.deal.curplayer not in self.user_seats:
            raise HTTPException(400, f"not your turn — {SEAT_LETTER[self.deal.curplayer]} to play")
        suit = SUIT_FROM_CHAR.get(suit_letter.upper())
        rank = RANK_FROM_CHAR.get(rank_letter.upper())
        if suit is None or rank is None:
            raise HTTPException(400, f"bad card {suit_letter}{rank_letter}")
        legal = list(self.deal.legal_moves())
        match = next((c for c in legal if c.suit == suit and c.rank == rank), None)
        if match is None:
            raise HTTPException(400, "card is not a legal move")
        self._play_card(match)

    def auto_play_until_user(self):
        """After a user play, run DDS for any defender/dummy-seat-the-computer-controls turns
        until it's user's turn again, or the deal completes."""
        while not self.complete and self.deal.curplayer not in self.user_seats:
            card = dds_pick(self.deal)
            self._play_card(card)

    def _apply_card(self, card):
        """Advance the deal + bookkeeping by one card. Does NOT touch move_log."""
        seat = self.deal.curplayer
        self.current_trick_plays.append({"seat": SEAT_LETTER[seat], "card": card_to_display(card)})
        self.deal.play(card)
        self.cards_played_count += 1
        if len(self.current_trick_plays) == 4:
            winner = self.deal.curplayer
            if winner in (Player.north, Player.south):
                self.ns_tricks += 1
            else:
                self.ew_tricks += 1
            trick_n = len(self.trick_history) + 1
            self.trick_history.append({
                "n": trick_n,
                "leader": self.current_trick_plays[0]["seat"],
                "plays": list(self.current_trick_plays),
                "winner": SEAT_LETTER[winner],
            })
            self.current_trick_plays = []
            if trick_n == 13:
                self.complete = True

    def _play_card(self, card):
        """Record card in the move log and apply it. Used by all play paths."""
        self.move_log.append(card)
        self._apply_card(card)

    def _rebuild_to(self, target: int):
        """Reset the deal to its initial state, then replay move_log[:target]."""
        new_deal = Deal()
        for seat in (Player.north, Player.east, Player.south, Player.west):
            new_deal[seat] = str(self.initial_hands[seat])
        new_deal.first = self.leader
        new_deal.trump = self.trump
        self.deal = new_deal
        kept = self.move_log[:target]
        self.move_log = []
        self.trick_history = []
        self.current_trick_plays = []
        self.cards_played_count = 0
        self.ns_tricks = 0
        self.ew_tricks = 0
        self.complete = False
        for c in kept:
            self.move_log.append(c)
            self._apply_card(c)

    def undo_to_checkpoint(self):
        """Pop the most recent /play (or /claim) checkpoint and rebuild to it.
        Returns True if any cards were undone."""
        if not self.undo_stack:
            return False
        target = self.undo_stack.pop()
        if target >= self.cards_played_count:
            return False
        self._rebuild_to(target)
        return True


# ---------- API ----------

app = FastAPI()
SESSIONS: dict[str, Session] = {}


@app.get("/api/scenarios")
def list_scenarios():
    files = sorted(p.stem for p in BBA_DIR.glob("*.pbn") if not p.stem.startswith("-"))
    return {"scenarios": files}


LAYOUT_PATHS = [
    REPO_ROOT / "btn" / "-button-layout-release.txt",
    REPO_ROOT / "btn" / "-button-layout-beta.txt",
]


def parse_layout(text: str):
    """Parse the .btn/-button-layout-*.txt format into ordered sections.
    Returns: list of {"title": str, "scenarios": [str, ...]} in source order."""
    import re
    sections = []
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"\[Section\]\s*(.+)$", line)
        if m:
            current = {"title": m.group(1).strip(), "scenarios": []}
            sections.append(current)
            continue
        if line.startswith("[Major]") or line.startswith("[Action]"):
            continue
        if line.startswith("---"):
            continue
        if current is None:
            continue
        # Scenario line — possibly with parenthesized groups, :color suffixes, --- as placeholder.
        # Collapse parens, then split by commas.
        flat = line.replace("(", "").replace(")", "")
        for part in flat.split(","):
            tok = part.strip()
            if not tok or tok == "---":
                continue
            # Strip :color or :width suffix
            tok = tok.split(":", 1)[0].strip()
            if tok and tok not in current["scenarios"]:
                current["scenarios"].append(tok)
    return sections


@app.get("/api/menu")
def get_menu():
    layout_path = next((p for p in LAYOUT_PATHS if p.exists()), None)
    available = {p.stem for p in BBA_DIR.glob("*.pbn") if not p.stem.startswith("-")}
    if layout_path is None:
        # Fallback: flat alphabetical
        return {"sections": [{"title": "Scenarios", "scenarios": sorted(available)}]}
    sections = parse_layout(layout_path.read_text())
    # Filter to scenarios that actually have a playable bba/*.pbn
    out = []
    for sec in sections:
        scenarios = [s for s in sec["scenarios"] if s in available]
        if scenarios:
            out.append({"title": sec["title"], "scenarios": scenarios})
    return {"sections": out}


class StartSessionBody(BaseModel):
    scenario: str
    board_index: int = 0
    role: str = "declarer"


@app.post("/api/session")
def start_session(body: StartSessionBody):
    path = BBA_DIR / f"{body.scenario}.pbn"
    if not path.exists():
        raise HTTPException(404, f"scenario not found: {body.scenario}")
    with open(path) as f:
        boards = list(pbn.load(f))
    if not boards:
        raise HTTPException(500, "scenario has no deals")
    idx = body.board_index % len(boards)
    board = boards[idx]
    try:
        sess = Session(board, role=body.role)
    except ValueError as e:
        raise HTTPException(400, str(e))
    # If role is declarer and user controls leader, fine. If user is declarer but not leader,
    # auto-play any DDS seats up to user.
    sess.auto_play_until_user()
    sid = secrets.token_urlsafe(12)
    SESSIONS[sid] = sess
    return {"session_id": sid, "state": sess.state()}


@app.get("/api/session/{sid}")
def get_state(sid: str):
    sess = SESSIONS.get(sid)
    if sess is None:
        raise HTTPException(404, "session not found")
    return {"state": sess.state()}


class PlayBody(BaseModel):
    suit: str
    rank: str


@app.post("/api/session/{sid}/play")
def play(sid: str, body: PlayBody):
    sess = SESSIONS.get(sid)
    if sess is None:
        raise HTTPException(404, "session not found")
    sess.undo_stack.append(sess.cards_played_count)  # checkpoint BEFORE user play
    sess.play_user_card(body.suit, body.rank)
    sess.auto_play_until_user()
    return {"state": sess.state()}


@app.post("/api/session/{sid}/undo")
def undo(sid: str):
    sess = SESSIONS.get(sid)
    if sess is None:
        raise HTTPException(404, "session not found")
    sess.undo_to_checkpoint()
    return {"state": sess.state()}


@app.post("/api/session/{sid}/replay")
def replay(sid: str):
    sess = SESSIONS.get(sid)
    if sess is None:
        raise HTTPException(404, "session not found")
    sess._rebuild_to(0)
    sess.undo_stack = []
    sess.auto_play_until_user()  # re-do the opening lead
    return {"state": sess.state()}


@app.post("/api/session/{sid}/claim")
def claim(sid: str):
    sess = SESSIONS.get(sid)
    if sess is None:
        raise HTTPException(404, "session not found")
    if sess.complete:
        raise HTTPException(400, "deal already complete")
    # Checkpoint so the user can undo a claim if they want to keep playing.
    sess.undo_stack.append(sess.cards_played_count)
    while not sess.complete:
        card = dds_pick(sess.deal)
        sess._play_card(card)
    return {"state": sess.state()}


@app.delete("/api/session/{sid}")
def end_session(sid: str):
    SESSIONS.pop(sid, None)
    return {"ok": True}


# ---------- static files ----------

@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
