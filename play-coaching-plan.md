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

Up to three files per **theme** (at a difficulty level), one per **seat**
(LHO/RHO/Declarer), pre-rotated, single track each — **theme-based, NOT
scenario-based**: a deal is *pulled* from a scenario, but the deck is keyed to its
teaching theme + level, never to one scenario. All
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

---

## 2026-06-25 — Defense build plan (design-session decisions)

**Scope.** Three "Basic" **DEFENSE** sets — **NT, Major, Minor** — 30 deals each,
student = South **defends**. The defending mirror of the `Basic_*` (declaring)
family.

**Lesson identity — THEME-based + LEVEL-based + ROLE-based, NOT scenario-based.**
Bidding lessons ≡ scenario names (1:1 with a `.btn`). Play lessons are the
opposite: each is a **theme** (Leads, Signals, Trump threats, Counting,
Inferences, …) at a **difficulty level** (beginner / intermediate / advanced),
for one **role/seat** (LHO / RHO / Declarer — see Seat axis), curated from
**many** scenarios. The level sets the **bidding complexity** — a *beginner* deck
pulls deals with beginner-level (natural, no-convention) bidding. A deal is
*pulled* from a scenario, but the deck is keyed to its theme + level + role,
**never to one scenario** — decoupled from `-PBS.txt`; each deal carries source
**provenance** (`[OriginalSource …]`). So source from *any* scenario whose
bidding fits the level, then select by theme.

**Seat axis.** Play lessons span three student seats: **LHO** (lead + defense),
**RHO** (third-hand defense), **Declarer**. Dummy has no decisions → no deck.
Taxonomy: **theme × difficulty-level × role/seat** (LHO/RHO/Declarer; contract type — NT/Major/Minor — is
context within a theme); seat goes in the filename
(`Scenario_LHO`/`_RHO`/`_Declarer`). Engine asymmetry: **LHO** needs a new
*graded-lead* anchor (the student leads); **RHO** rides the existing
`[ROLE leader]` auto-play (partner leads), then plays third-hand.

**Contract level (game vs partscore — distinct from the *difficulty* level
above).** *Not* a deck axis — the core job (count declarer's tricks, set up +
cash yours, try to set it) is the same whether they're in game or a partscore, so
a deck can mix 1N/2N/3N. (The MP partscore-overtrick nuance — passive vs a
partscore, all-out vs a game — is advanced, deferred.)

**Folders (target, from-scratch).** `bid/` and `play/`, **both non-rotated**. The
current `coaching-curated → coaching → coaching-non-rotated` chain exists *only*
to feed the Play Trainer's **runtime** rotation (what the `@`-tokens serve); with
Bridge Classroom (a non-rotated dumb renderer) as the home, that dimension
collapses. Defense lives in `play/` (all seats), **not** a defense-specific
folder. `play/` is greenfield → adopt the clean model now; existing **bid**
lessons migrate later, on Rick's timeline. **Interim (now, per David):** leave the
existing **bid** lessons — and the existing declarer-play lessons — in
`coaching-non-rotated/`, untouched; only the **new** play/defense content goes in
the new `play/` folder. The `bid/` folder and the migration are deferred.

**Fork shortcut (David's idea).** To run the fork in the *target* `bid/` + `play/`
shape *now* without waiting on migration, **mirror** `coaching-non-rotated/` into
the fork's folders — bidding lessons → `bid/`, the existing declarer-play sets →
`play/` (joining the new defense). Make it a **regeneratable copy** (gitignored;
re-run a one-line copy whenever `coaching-non-rotated/` changes), so the single
source of truth stays `coaching-non-rotated/` and the two never drift. Rick's
production still reads `coaching-non-rotated/`, untouched. The fork then runs
exactly like the eventual merged Classroom.

**Anchors / fade.** No `@`-tokens (rotation-only; these sets are pre-rotated /
fixed-South — write 2nd person). Reuse the `⟦ ⟧` fade (verbose-on-wrong,
nod-on-right, partner always shown). **Missing:** a graded opening-**lead** anchor
(the lead counterpart of `[BID]`/`[ACCEPT]`). Defender `[PLAY]` parked.

**Don't break Rick's live BC.** Classroom reads the **existing** layout off raw
GitHub main. All changes **additive + backward-compatible**; nothing reaches BC
until commit + push (and no breaking pushes).

**Build strategy — David's BC fork.** Build the **whole vertical** — PBS content
*plus* the BC engine work (defender seating, reveals, graded-lead anchor,
defender `[PLAY]`) — in **David's fork** of Bridge Classroom. Rick's production
stays untouched **and** we stop waiting on his parser. **Downside-resilient:** the
PBS content is renderer-agnostic and survives even if Rick passes; the
proof+design de-risk his version; only the fork engine code is throwaway. Then
offer Rick a working, tested merge.

**Status.** Pilot board drafted: `Basic_NT` b13 rotated → an **NT-LHO** lesson in
`coaching-curated/Basic_NT_Defense.pbn` (mis-homed — moves to `play/`). ⚠️ BC
handling defense deals is **unverified** — test one deal in a local BC run before
assuming it renders (every BC lesson so far has the student on the *declaring*
side).

**Play selection (menu).** BC's "Pick a Scenario" is built from
`btn/-button-layout-release.txt` (`[Section]` + rows of **scenario** names →
load a `.btn`). Theme-named play lessons have no `.btn`, so they can't be buttons
there. Fix: a **parallel play menu** — a play-layout file (the play counterpart
of `-button-layout`, *same* `[Section]`/rows format, **seat-aware**: e.g.
`[Section] Notrump Defense` → `Basic_NT_LHO`, `Basic_NT_RHO`) read by a **play
picker** in the fork ("Pick a Play Lesson" / a Play tab) that loads from `play/`.
Reuses BC's existing menu renderer (new bits = which file it reads + a click that
loads a play lesson, not a scenario). Additive — Rick's scenario selector
untouched. The 12 existing declarer-play sets are currently scenario-buttons in
`-button-layout`; in the fork-mirror world they graduate into the play menu with
the defense (leave them in both for now, move at cutover).

**Open.** Folder name; split "Basic NT Defense" into `_LHO`/`_RHO`; the
provenance tag; the graded-lead anchor shape; play-menu layout-file location/name;
heads-up note to Rick (drafted).
