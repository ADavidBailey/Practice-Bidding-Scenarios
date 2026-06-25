# Rough Plan — Coaching Play

*Draft, 2026-06-25. Synthesized from a design discussion; not yet built.*

**Goal:** extend play coaching beyond declarer to all three playable seats, picking the
right deals per seat instead of forcing one deal to teach everything.

## Principles

1. **Topics attach to seats.** Opening Lead, Declarer Play, Signaling, Counting Cards,
   Counting Points, Inferences from the Bidding — each maps to the seat(s) where it
   applies. (Signaling: defenders emit and read; declarer reads *and* disrupts via
   falsecards.)
2. **Four seats, named from declarer's frame** (clockwise: Declarer → LHO → Dummy → RHO).
   Three carry lessons — **Declarer** (declarer play), **LHO** (opening lead, then
   defense), **RHO** (third-hand defense). **Dummy** has no decisions, so no deck. LHO/RHO
   names the two defenders precisely (LHO leads then defends; RHO is third hand). NB: the
   on-disk marker still reads `[ROLE leader]` (≡ LHO) and `[ROLE declarer]`; renaming the
   marker string touches the trainer parser (Rick's side) — adopt LHO/RHO only in our
   vocabulary + deck/file names for now.
3. **Switch roles → switch deals.** A deal earns coaching per seat, on that seat's own
   merits. Bias to drop.
4. **Select-then-grade.** Scenario selection gets the role cheaply; one double-dummy
   solve read three ways finds the actual decision and drops the flat hands.
5. **Use LHO/RHO directly** in student-facing prose, beginners included (David's call,
   2026-06-25 — happy with LHO/RHO now). The terminology *fade* (Leader → Left Hand
   Opponent (LHO) → LHO) is possible but **not** required — add it only if Rick judges
   beginners need the gentler ramp. Prose only either way; the `[ROLE]` markers are
   untouched regardless.

## Where we stand (verified 2026-06-25)

- 12 play sets, 349 boards, **100% declarer.** `[ROLE defender]` count = 0; no E/W
  declarer on any curated play board. Opening-lead and defender decks do not exist —
  the `[ROLE leader]` markers are the opponents' auto-played opening lead, not the
  student leading.
- ~13 boards put the student in the dummy seat (partner declares) — a defect the grade
  should catch and drop.
- Corpus: `bba/` has 345 scenarios / 171,446 deals. N/S declares 80%, defends 20%.

## Sources (no new generation needed for defense)

**Rotation is the key.** A 90°/270° spin swaps the N/S↔E/W axis, seating the student in a
defender's chair. So the ENTIRE library — not just deals where the opponents already
declare — becomes a defender/lead source. (Rotate dealer + vulnerability tags too; the
4-player rotate tooling already does this.) Three streams:

- **Defending CONSTRUCTIVE auctions (rotate the whole library)** → take any of the ~137k
  N/S-declares deals and rotate 90°; the student defends a normal auction (Stayman 3NT,
  Jacoby game, slam). Largest, most realistic defensive pool.
- **Defending COMPETITIVE auctions (no rotation)** → the 49 defense-heavy scenarios where
  N/S already defends (Lead_Directing_Double, Responsive_Double, the overcall/double
  families). Advanced — not for beginners.
- **BEGINNER defense = rotate beginner-level CONSTRUCTIVE scenarios**, selected by bidding
  *content/level*, NOT the "Basic" filename. The beginner then defends the very auctions he
  just learned to bid — no new bidding concept. The pool is far larger than the `Basic_*`
  family: e.g. Major_Opener (79% declares), Major_Suit_Fit (89%), Minor_Suit_Opener,
  alongside Basic_NT/Major/Minor. **Basic_NT rotated is the prime opening-lead source**
  (lead/defense vs 1NT–3NT, the canonical beginner lead lesson), richest because it was
  ~97% declarer and thus useless as defense until rotated. Criterion = *constructive AND
  uses only bidding the student knows.* EXCLUDE for true beginners: competitive auctions
  (Basic_Overcall/Takeout — a takeout double is itself a concept) and convention-laden
  constructive ones (Jacoby_2N, Bergen, Splinters, Gavin_*) until the student has met that
  convention.

- **Declarer decks** → as today (no rotation).
- **Auction-independent technique lessons** → purpose-built `.btn` (full deal + pinned
  spot cards). Later.

**Selection (all rotated sources).** Rotation multiplies SEATS, not LESSONS — the
defenders' hands and spot cards were unconstrained, so most rotated hands are flat. The
per-seat grade gates; bias to drop. The grade's difficulty score is a **band-pass, not a
sort key**: beginner decks take the LOW band, advanced decks the HIGH band. So for a
beginner the grade does two jobs — clears the "is there a decision worth teaching" bar AND
**caps difficulty so the hand stays simple**: a clear rule-based action (textbook lead —
top of a sequence, fourth-best, partner's suit; an obvious defensive plan), normal shape
(no freaks), one teaching point, no advanced technique (no required count, trump promotion,
endplay, squeeze). Advanced decks want the opposite end — the hard hands are the good ones.

## Packaging

Up to three files per scenario, one per role, pre-rotated, single track each. All
content-side; reuses the existing pipeline. (The "one file, three grades + three tracks"
data model is prettier but deferred — it needs present-time rotation + track selection in
the engine.)

## Coaching modes

- **Full coaching** — author prose → gate → promote.
- **Un-coached play** — engine toggle: play a curated deal with prose off. For defense the
  engine must play the other seats adaptively and score against double-dummy par. (Engine
  work, Rick's side; small.)
- **Difficulty ladder** — cold → reveal coaching → graduate to no coaching.

## Shortest path

1. Build the per-seat play grade (DD-based; pass/fail + difficulty). Also flags the
   dummy-defect boards.
2. Pilot one **beginner opening-lead (LHO) deck by rotating Basic_NT** (lead/defense vs
   1NT–3NT): select → grade → author.
3. Add one **defender deck** from a defense-heavy scenario.
4. Enable **un-coached play** so every curated deal is also playable cold.

## Open decisions

- Beginner vs. advanced split for the new decks.
- Whether to keep a rare "same deal, three chairs" multi-perspective format.
- Role-file naming: `Scenario_Declarer` / `Scenario_LHO` / `Scenario_RHO` (underscores
  only — hyphens break the BBO/classroom regex).
- *(Resolved)* Terminology: LHO/RHO used directly, beginners included; fade deferred unless Rick wants it.
