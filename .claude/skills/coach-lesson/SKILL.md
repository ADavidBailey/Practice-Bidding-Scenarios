---
name: coach-lesson
description: >
  Author a complete both-seats coaching lesson for a BBA-NATIVE bidding scenario
  and produce all served artifacts in one consistent pass: curate the pool →
  tokenized coaching-curated/<scn>.pbn → gated promote to served coaching/<scn>.pbn →
  resolve to South=student coaching-non-rotated/<scn>.pbn (bridge-classroom) →
  update both toc.json files. Invoke as `/coach-lesson <Scenario>` (e.g.
  `/coach-lesson Fourth_Suit_Forcing`). Use ONLY for conventions BBA bids natively
  (its bba/<scn>.pbn [Auction] is the answer key — Basics, New_Minor_Forcing,
  Fourth_Suit_Forcing). For conventions BBA CANNOT bid (Spiral Raises), use the
  py/spiral_auction.py substitution path instead — not this skill.
---

# coach-lesson — bootstrap a full coaching lesson for a BBA-native bidding scenario

`$ARGUMENTS` is the scenario name (a `btn/<Scenario>.btn` stem, e.g.
`Fourth_Suit_Forcing`). Call it `<scn>` below. Run everything from the project root.

## Precondition check (do this first)
1. Confirm `btn/<scn>.btn` exists and its `# bba-works:` is `true` (BBA bids the
   convention natively). If BBA can't bid it, STOP — this is the spiral-auction path,
   not this skill.
2. Confirm the dealer pipeline through `bba/` is present: `bba/<scn>.pbn` and
   `bba-filtered/<scn>.pbn`. If missing, the upstream pipeline (`dlr→pbn→rotate→bba→
   filter`) must run first (Windows VM for bba) — flag to David; don't fake it.
3. Read `btn/<scn>.btn`'s `/*@chat */` block — it is the convention's source of truth
   (what each call shows, plus any partnership-agreement caveats). Read the
   bridgebum/reference URL it cites if present.
4. Note the **seats**: most of these deal `dealer north`, so North opens and **South
   (the student) makes the hero call**. Verify by reading a few `bba/<scn>.pbn`
   `[Auction]` blocks and mapping calls to seats by dealer.

The sibling **New_Minor_Forcing** is the canonical worked example of this whole flow —
inspect its artifacts when unsure.

## Phase 1 — Curate (→ bba-curated/<scn>.pbn)
Grade the filtered pool and annotate it, exactly as for New_Minor_Forcing (design:
`pbn-curation-plan.md`).
- Layer A features: `python3 -P py/curate.py <scn>` (resumable; reads the `.btn`
  `# curate:` directive).
- Layer B grading: fan out subagents to grade each board's BIDDING
  (textbook / standard / judgment / reject) per the rubric in `pbn-curation-plan.md`;
  write verdicts to `bba-curated/<scn>-graded.json`. Borderline-but-defensible calls
  are **judgment + also_ok**, never reject (board-137 calibration).
- Annotate: `python3 -P py/annotate.py <scn>` → inserts `{Curate ...}` blocks into
  `bba-curated/<scn>.pbn`.

## Phase 2 — Author the tokenized lesson (→ coaching-curated/<scn>.pbn)
This is the rich, both-seats, rotation-ready artifact. Voice + structure spec:
`coaching-curated/GENERATOR.md`. Read it.
1. `python3 -P py/coach.py packets <scn> "bidding=textbook,judgment" "diff<=3" -n 30`
   → selects ~30 decision-rich boards, writes packets to `coaching-curated/.work/`.
2. Subagents author the prose per packet using the **rotation pronoun tokens** so the
   lesson renders for either seat (`@S` / `@s`, `@Your` / `@your`, `@v(base|third)` —
   parens, not braces; use `@S` at most once per chunk). Rules:
   - one `[BID <call>]` anchor per **N/S non-pass call** (both seats get anchors here —
     rotation may seat the student in either); a framing-only intro before the first;
   - describe what each call SHOWS by agreement — never the actor's concrete hidden
     holding during the auction;
   - `[ACCEPT <call>]` on any genuine judgment alternative;
   - close each board with `[show NS]` + a short result reflection; suit symbols
     `\S \H \D \C`; plain commas.
   Write `coaching-curated/.work/<scn>-coach*.json` as `{board, coaching}` objects.
3. `python3 -P py/coach.py splice <scn>` → builds `coaching-curated/<scn>.pbn`.
4. `python3 -P py/coach.py validate <scn>` → must report **0 issues** (marker
   structure + suit-quality + ordering lint; "solid" only when the suit truly is
   AKQ-solid — see GENERATOR.md).

## Phase 3 — Promote to served (→ coaching/<scn>.pbn)
`python3 -P py/promote.py <scn>` — gated copy of coaching-curated → coaching. It only
promotes if all gates pass; it reports blocked scenarios and exits non-zero on any
block. **Only commit YOUR scenario's promoted file**; if promote.py syncs other
eligible scenarios too, flag them, don't claim them.

## Phase 4 — Resolve to South=student (→ coaching-non-rotated/<scn>.pbn)
There is **no committed automation** for this step yet — do it deterministically by
hand/agent, then post-process. The non-rotated file differs from the tokenized one in
TWO ways: tokens resolved for a fixed South seat, AND partner's anchors folded.
1. **Resolve tokens** for South=student (the trainer's `fill_pronouns` logic):
   - a call made by **South** renders 2nd person: `@S`→"You", `@s`→"you",
     `@Your`→"Your", `@v(base|third)`→its **base** text;
   - a call made by **North** renders 3rd person: `@S`→"Your partner",
     `@Your`→"Your partner's", `@v(base|third)`→its **third** text.
2. **Fold partner calls** (the bridge-classroom discipline): bridge-classroom renders
   markers literally and only the student is quizzed, so:
   - keep a `[BID <call>]` anchor on **every South call, and only South's calls**;
   - **remove** partner's (North's) `[BID]` anchors and merge that explanation into the
     adjacent South chunk, in 3rd person ("your partner opens 1\D …");
   - anchor South's **auction-ending Pass** with `[BID Pass]` when South's final call
     ends the auction;
   - put **each `[BID …]` anchor on its own line**;
   - open the block with `[show S]` + a one-line seat-neutral intro; keep `[show NS]`
     at the close.
   Model the exact shape on a CLEAN non-rotated file — `coaching-non-rotated/Basic_Minor.pbn`
   or `coaching-non-rotated/Spiral_Raises_Wolpert.pbn`. **Do NOT model on
   `coaching-non-rotated/New_Minor_Forcing.pbn`, `Basic_Overcall.pbn`, or
   `Basic_Takeout_Double.pbn`** — those still carry un-folded partner anchors (a known
   defect to be fixed, not copied).
3. **Post-process:** `python3 -P py/bridge_classroom.py <scn>` — strips pre-auction
   `{Shape}/{HCP}/{Curate}` blocks, renumbers `[Board]` 1..n, preserves `[OriginalBoard]`,
   ensures the coaching block opens with `[show S]`. Idempotent.

## Phase 5 — Verify (all must pass before declaring done)
- **Anchor check** (the load-bearing gate): parse each non-rotated board's auction by
  dealer-seat; assert every `[BID]` maps to a South call, every South non-pass call is
  anchored, and **no partner call carries an anchor**. (Reuse the parse-by-seat check
  used to audit the existing files.)
- `coaching-non-rotated/<scn>.pbn` has **0** `@S/@v(/@Your` tokens left.
- All boards parse via `endplay` (the trainer's loader) in all three of
  coaching-curated / coaching / coaching-non-rotated.
- No hidden-hand reveal mid-auction; suit symbols render; ~4 coaching beats/board.
- **toc.json**: add the lesson to BOTH `coaching-curated/toc.json` and
  `coaching-non-rotated/toc.json` under the right category (e.g. "Minor/Major
  Sequences"): `id: <scn>`, a human `name`, one-line `description`, `difficulty`.
  Re-validate both as JSON.

## Report
List the boards chosen, the validate + anchor-check results, the promote.py output
(what it promoted/blocked), and any judgment calls. Commit only when David asks
("commit" = commit + push). Committing a coaching change means committing its
regenerated derived files too (curated + served + non-rotated + toc), or GitHub serves
stale and the menu shows MISSING/ORPHAN.

---
**First use:** `/coach-lesson Fourth_Suit_Forcing` — after 1♣/1♦/1♥, a 1-level
response, and a new suit by opener, the **fourth suit is artificial and game-forcing**;
dealer North, so South (student) makes the 4SF call; BBA bids it natively
(21GF-SPECIALS NS / 21GF-GIB EW).
