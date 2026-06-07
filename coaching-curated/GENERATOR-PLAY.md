# Play-coaching generator — authoring spec

How the **card-play** coaching for the 12 play scenarios (Finesses, Notrump
Play, Suit Contract Play) is written into `coaching-curated/<scenario>.pbn`.
This is the play counterpart of `GENERATOR.md` (bidding). It uses the trainer's
EXISTING `[ROLE]/[STAGE]` tip machinery — no trainer changes needed.

The student declares (South) and the lesson teaches one play technique (the
board's curated `declarer` theme: hold-up, finesse-safe-hand, establish-long-
suit, ruff-in-dummy, …). Selection comes from the curation: pick boards graded
`declarer: textbook`/`standard` for the target theme (and, for hold-up,
`holdup_required: true` from Layer A).

## What goes in the `{ ... }` block

Per board, after the `[Auction]`, the block holds an optional brief bidding
part (these auctions are short/fixed — keep it minimal or omit) followed by
the PLAY TIPS, which are `[ROLE r][STAGE s]`-anchored chunks. The trainer
fires each tip at its stage. Stages: `auction-end`, `pre-lead`, `post-lead`,
`post-play`. Roles: `declarer`, `leader`, `defender`.

Emit these tips (declarer-focused; the UI centers on declarer):

1. `[ROLE leader][STAGE pre-lead]` — **REQUIRED and load-bearing.** It MUST
   start with `Lead the \Xr` naming a SPECIFIC card, suit escape directly
   before the rank, NO space (`\HK`, never `\H K` — a space stops the parser
   extracting the card for the auto-lead). The card is the correct standard
   opening lead from the OPENING LEADER's hand (declarer's LHO = West when
   South declares):
   - vs notrump: 4th-best from the longest, strongest suit (or top of a 3+
     touching-honor sequence).
   - vs a suit contract: a singleton, else partner's bid suit, else top of a
     touching-honor sequence, else 4th-best from the longest suit.
   - card from a holding: top of a sequence/interior sequence; 4th-best from
     length; low from three small; top of a doubleton; K from AK.
   One or two sentences, assertive (the leader sees their own hand).

2. `[ROLE declarer][STAGE auction-end]` — the plan BEFORE the lead: state the
   contract, count the sure winners (or losers in a suit contract), name the
   problem the theme poses, and the line. 2-4 sentences.

3. `[ROLE declarer][STAGE post-lead]` — fires AFTER the opening lead, so START
   from the actual lead: name what was led, the trick-1 decision (win / duck /
   which card), and what the lead suggests — but HEDGE the read (the card is a
   fact, its meaning an inference): "the \D2 looks like a fourth-best,
   suggesting about four" / "looks like top of a sequence, so West probably
   holds the QJ" / "looks like a singleton — watch for a ruff." Then walk the
   technique to the contract. 3-5 sentences.

4. `[ROLE declarer][STAGE post-play]` — the review: what mattered, why the
   technique worked, and PRAISE (this is the safe place for warmth). 2-3
   sentences.

(For defense scenarios add `[ROLE defender][STAGE post-lead]` from the
defender's vantage; same hedging rules.)

## Hard rules

- The pre-lead card is load-bearing and must be the leader's CORRECT standard
  lead, written `\Xr` with no space. Get this right — the trainer auto-plays it.
- Tips are written from ONE role's vantage and only mention what that role can
  see at that stage. The leader tip sees only the leader's hand; the declarer
  auction-end tip sees declarer + dummy (dummy is down after the lead for
  post-lead). Do NOT reveal a hand the role can't see.
- HEDGE declarer's reads of the defenders' cards (inferences, not facts).
- Defensive signals (attitude/count/suit-preference): NUANCED and OPTIONAL —
  the audience is beginner/senior and rarely signals reliably. Never state a
  signal as fact; hedge ("if they're signaling, that high card hints at…, but
  don't count on it"). Prefer concrete card-reading (rule of 11, who showed
  out) over signal theory.
- Suit escapes `\S \H \D \C` render as ♠♥♦♣.
- The winning line must be findable by PRINCIPLE (counting, the named
  technique), not double-dummy. The board was curated so the principled line
  succeeds and a careless line fails.

## Pipeline (parallels coach.py)

1. `coach.py play-packets <scenario>` — select curated boards for the theme,
   build packets {board, deal (all four hands, for the AUTHOR to reason about
   the play), contract, declarer, leader, theme, curate note, dd info}.
2. A subagent per packet writes the tips per this spec.
3. `coach.py play-splice <scenario>` — splice the tips after each board's
   auction; validate (pre-lead card present + no-space, [ROLE]/[STAGE] parse,
   endplay-parses).

## Later (needs a trainer change — coordinate, do not collide)

Per-trick coaching (`[STAGE trick N]` firing at the moment of the key play)
is a future enhancement: today the post-lead tip is one whole-hand plan. The
per-trick marker would let coaching fire exactly when the student is about to
make the critical play. Out of scope here; the current four stages are what
the trainer renders now.
