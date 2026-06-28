# Bridge Classroom — Change requests for Rick

> **STATUS: SENT to Rick 2026-06-28** — awaiting his review/decision. Nothing here has been
> merged into Rick's upstream yet; "built" means committed/pushed to **David's fork only**.

*Self-contained: written to be read cold, without PBS-internal context.*

Two parts: **Part A** — changes already built on David's fork, requesting review and
upstream merge. **Part B** — changes we'd like Rick to build or fix.

Fork: `https://github.com/ADavidBailey/Bridge-Classroom`.
- A1–A4 are on branch `main` (**18 commits ahead** of `Rick-Wilson/Bridge-Classroom@main`).
- **A5 (`[ACCEPT]`) is on a separate branch `accept-and-lesson-sync`** (off `fork/main`,
  +2 commits) — **not yet pushed**; merges cleanly on top of `main`.

---

## Part A — Built on our fork; requesting review + upstream merge

Listed newest-feature-first. "Frontend-only" = safe to merge independently; the report
button also adds a **server (Rust) route**, so it needs coordination with the API.

### A5. `[ACCEPT]` judgment-call scoring  *(frontend only)*
A coaching board can mark a second defensible call as also-correct with an inline
`[ACCEPT <call>]` marker, for judgment decisions with more than one sound call. Before,
BC scored the alternate wrong and the unrecognized tag leaked into displayed text.
- **Behavior:** parser pulls `[ACCEPT …]` into the bid step's `acceptedBids` and strips
  the marker; `makeBid` scores correct on the recorded call **or** any accepted call. The
  auction still advances on the recorded call. Purely additive — boards without `[ACCEPT]`
  are byte-identical, so existing lessons (Baker Bridge, the 5 bundled) are unaffected.
- **Files:** `src/utils/pbnParser.js`, `src/composables/useDealPractice.js`; tests in
  `src/utils/__tests__/pbnParser.test.js`, `src/composables/__tests__/useDealPractice.test.js`.
- **Branch/commits:** `accept-and-lesson-sync` — `6259eb0` (impl), `f0aee3c` (test).
- **Note:** the marker is supplied by PBS coaching content (PBS side, separate repo); this
  is just the engine that consumes it.

### A1. "Report a Problem" button  *(frontend + API)*
Lets a student flag a problem on a coached lesson from inside the app. Button sits beside
the bidding box; popup is draggable; report endpoint is configurable.
- **Files:** `src/components/ReportProblemModal.vue`, `src/composables/useReportProblem.js`,
  `src/views/MainLayout.vue`, `vite.config.js`; **API:** `bridge-classroom-api/src/routes/reports.rs`
  (+ `config.rs`, `main.rs`, `routes/mod.rs`, `.env.example`).
- **Commits:** `18b48a2`, `ee1fc79`, `07bd31e`, `4a3927f` (merge `54dc1f8`).
- **Note:** endpoint set via `VITE_REPORT_URL`; our local setup points it at a small relay,
  but the Rust route is the real server path — this is the piece to align with Rick.
- **Now opt-in per collection** (commit `07b618a`, on branch `accept-and-lesson-sync`):
  a report files an issue in the *content* repo, so the button shows only for a collection
  that sets `report: true` and points the endpoint at its own repo. **On for David Bailey
  Scenarios, off for Baker Bridge** — a report on a Baker board is about your content, not
  David's, so it shouldn't open an issue in his repo. **Rick: if you want it on Baker
  Bridge, say so** — it's one flag (`report: true` on the collection) plus pointing
  `VITE_REPORT_URL` at your repo; happy to wire it up or leave it to you.

### A2. Scenario @chat popup  *(frontend only)*
Shows the scenario's chat/teaching blurb in a sizable, movable popup; appears in Bidding
Practice and in coaching lessons; reopen button labeled "Description".
- **Files:** `src/components/ScenarioChatPopup.vue`, `src/views/MainLayout.vue`,
  `src/views/BiddingPracticeView.vue`.
- **Commits:** `d3add23`, `22dc2eb`, `8ef20f5`, `7159985`, `c41db3c`, `18b3d0e` (merge `d7834a2`).

### A3. Coaching-feedback fade — bids  *(frontend only)*
Three-mode feedback on a bid: correct call → brief *varied* affirmation + the
partner/opponent follow; wrong call → full explanation. Renderer reads the `⟦ ⟧` the
content wraps around the student's own justification; un-bracketed legacy content is
unchanged. Adds a board-level cheer (Bravo!/Perfect!) when every call on a board was right.
- **Files:** `src/utils/pbnParser.js`, `src/composables/useDealPractice.js`, `src/views/MainLayout.vue`.
- **Commits:** `c8a9f60`, `c5dd047`, `065b44e` (merge `add4958`).

### A4. Coaching layout  *(frontend only)*
Left-align the table during practice with the chat open on the right; re-center when the
description closes; cap coaching-text height to the window so the bid box stays in view.
- **Files:** `src/views/MainLayout.vue`.
- **Commits:** `4e484c8`, `15bc887`.

---

## Part B — Requests to build / fix

Each item ends with a **paste-ready Claude prompt**. If you use Claude Code, open it at
the root of your `Bridge-Classroom` checkout and paste the block — it'll read the repo and
propose the change as a diff for you to review. (Skip them if you'd rather do it by hand;
they're just a shortcut.)

### B1. BUG — `[showcards]` multi-seat tag is mis-parsed  *(small; bug)*
A `[showcards …]` tag that names **two seats** is parsed wrong.
- **Where:** `src/utils/pbnParser.js`, the seat regex `/([NESW]):([^,\s]+(?:,[^,\s]+)*)/gi`
  (~line 342).
- **Repro:** `[showcards N:C4,E:CT]` parses to `{ N: ["C4", "E:CT"] }` — the regex swallows
  `,E:CT` as a *second card of North*, so East is lost. The documented `E:S7,S:S5` form fails
  the same way.
- **Current workaround (in our PBN content):** a **space after the comma** (`N:C4, E:CT`)
  breaks the greedy match and parses correctly. So existing files work, but the documented
  no-space format is broken.
- **Proposed fix** (verified against all cases below) — replace the regex loop with a split
  on "comma that precedes a seat token":
  ```js
  for (const part of showcardsValue.split(/,(?=\s*[NESW]:)/)) {
    const i = part.indexOf(':'); if (i < 0) continue
    const seat = part.slice(0, i).trim().toUpperCase()
    const cards = part.slice(i + 1).split(',').map(c => c.trim().toUpperCase())
    if (seat) showcards[seat] = cards
  }
  ```
- **Acceptance:** `N:C4,E:CT` and `E:S7,S:S5` → two seats; `E:S7,H3,S:S5` → E has two cards,
  S one; `N:C4,C7` → one seat, two cards; spaced variants (`N:C4, E:CT`) still parse the same.
- **Claude prompt:**
  ```
  In src/utils/pbnParser.js, fix the [showcards ...] parser so a tag naming two seats
  parses correctly. The seat regex near line 342, /([NESW]):([^,\s]+(?:,[^,\s]+)*)/gi,
  greedily swallows the next seat as a card, so [showcards N:C4,E:CT] becomes
  { N: ['C4','E:CT'] } and East is lost. Replace the matching loop with a split on a
  comma that precedes a seat token:
    for (const part of showcardsValue.split(/,(?=\s*[NESW]:)/)) {
      const i = part.indexOf(':'); if (i < 0) continue
      const seat = part.slice(0, i).trim().toUpperCase()
      const cards = part.slice(i + 1).split(',').map(c => c.trim().toUpperCase())
      if (seat) showcards[seat] = cards
    }
  Then add a vitest case. It must pass: N:C4,E:CT and E:S7,S:S5 -> two seats;
  E:S7,H3,S:S5 -> E has two cards and S one; N:C4,C7 -> one seat with two cards; and the
  spaced form N:C4, E:CT still parses the same.
  ```

### B2. BUG — header title overprints the greeting  *(small; cosmetic CSS)*
On a long collection/lesson title (e.g. "…Bailey Scenarios - Third Hand vs Notrump"), the
`<h1>` title and the "Welcome back, David" greeting render on top of each other.
- **Where:** `src/views/MainLayout.vue` — `<header class="app-header">` (h1 ~line 18,
  greeting span line 19). Cause: `.welcome-greeting` is `position: absolute; left: 50%`
  (centered, ~line 1366), drawn over the flex header; the h1 has no max-width/ellipsis, so a
  long title reaches the center and collides.
- **Requested:** title and greeting never overlap on any title length.
- **Options (Rick's call):** (a) take `.welcome-greeting` out of absolute positioning and let
  it sit in the flex flow; (b) truncate the h1 with `min-width:0; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap` and a max-width that stops before center;
  (c) hide the centered greeting on lesson views.
- **Claude prompt:**
  ```
  In src/views/MainLayout.vue, fix the app header so a long collection/lesson title never
  overlaps the "Welcome back, ..." greeting. The greeting span (.welcome-greeting, ~line
  1366) is position: absolute; left: 50%, drawn over the flex header, and the h1 title has
  no max-width or ellipsis, so a long title collides with it. Pick the cleanest fix: either
  move .welcome-greeting into the normal flex flow, or truncate the h1 (min-width:0;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap, plus a max-width that stops
  before center), or hide the centered greeting on lesson views. Verify with a long title
  like "David Bailey's Scenarios - Third Hand vs Notrump".
  ```

### B3. ENHANCEMENT — per-card (lead/play) 3-tier feedback  *(medium)*
The **bid** version is built (A3, on the fork). Requested: the same fade for **card**
decisions (opening leads and third-hand play). Today a wrong card shows the same text regardless of which card
was chosen. Respond to the *actual* choice — correct (terse nod) / reasonable ("good thought,
but…") / wrong (full why) — with length fading by correctness.
- **Claude prompt:**
  ```
  Extend Bridge Classroom's 3-tier feedback fade from bids to card plays. For bids it
  already works: a correct call shows a brief affirmation, a wrong call the full
  explanation, reading the brackets the content wraps around the student's own
  justification (see src/composables/useDealPractice.js makeBid and the parsing in
  src/utils/pbnParser.js). Do the same for card decisions (opening leads and third-hand
  play): respond to the actual card chosen -- correct (terse nod) / reasonable ("good
  thought, but...") / wrong (full why) -- with the explanation length fading by
  correctness. Today a wrong card shows the same text no matter which card was chosen.
  Propose the content markup and the engine changes before implementing.
  ```

### B4. ENHANCEMENT — full defender play-out with revert-and-correct  *(large)*
Let the student defend the **whole** hand card-by-card (not just the opening lead). A mis-play
is reverted and the correct card substituted, then play continues — the declarer-play model
applied to a defender (South).
- **Status:** prototype + build-ready handoff spec already on our fork, branch
  `defender-playout-investigation` (commits `d753cab`, `23be662`, `aa9c9a5`). Ready to build
  when chosen.
- **Claude prompt:**
  ```
  Build full defender play-out in Bridge Classroom: let the student (South) defend the whole
  hand card by card, not just the opening lead. A mis-played card is reverted and the correct
  card substituted, then play continues -- the declarer-play model applied to a defender. A
  prototype and a build-ready handoff spec already exist on the branch
  defender-playout-investigation (commits d753cab, 23be662, aa9c9a5). Check out that branch,
  read the spec, and integrate it into the main play flow.
  ```

### B5. NICETY — remember the previous attempt on revisit  *(small; optional)*
Returning to a completed deal resets it to the start (a clean re-try) — fine as-is. Optional
improvement: remember the previous lead/play + result instead of fully resetting.
- **Claude prompt:**
  ```
  In Bridge Classroom, when a student revisits a completed deal it currently resets to the
  start for a clean re-try. Add an option to instead remember the previous lead/play and
  result and show it on revisit, while keeping the clean-retry behavior available. Find where
  a deal is reset on load (the play / deal-practice composables) and add the
  remembered-attempt path.
  ```

### B6. FIX — affirmation verb on lead lessons  *(tiny)*
On a lead/defense lesson the success cheer can read with bid wording ("Beautifully bid!").
Use the verb that matches the lesson type ("Well led!").
- **Claude prompt:**
  ```
  In Bridge Classroom, the success affirmation on a lead/defense lesson can use bid wording
  ("Beautifully bid!"). Make the verb match the lesson type so a card-play lesson says "Well
  led!" instead of "...bid!". Find where the affirmation/cheer text is chosen (search for the
  bid affirmations / board-celebration logic, around src/views/MainLayout.vue) and branch on
  whether the current step is a card play or a bid.
  ```

---

## How the coaching content is authored  *(FYI — reusable if you want it)*

The lessons aren't written board by board. The `{...}` coaching prose is generated by
**Claude subagents following a fixed authoring spec**, then mechanically spliced into the
PBN — so the voice stays consistent and the volume is feasible. If you ever want to author
or extend lessons the same way (for Baker Bridge or anything else), the whole pipeline lives
in the PBS repo and is yours to reuse:

- **Authoring spec — bidding:** [`coaching-curated/GENERATOR.md`](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/coaching-curated/GENERATOR.md)
  — the rules a subagent follows: the token-free South-fixed format, the `⟦ ⟧` brackets the
  feedback fade reads, and the structure discipline that makes `[ACCEPT]` work.
- **Authoring spec — play:** [`coaching-curated/GENERATOR-PLAY.md`](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/coaching-curated/GENERATOR-PLAY.md)
  — the same, for card-play lessons.
- **Orchestration:** [`.claude/skills/coach-lesson/SKILL.md`](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/.claude/skills/coach-lesson/SKILL.md)
  — the `/coach-lesson <Scenario>` skill that runs the full pass (curate → author → gate → resolve).
- **Mechanical steps:** [`py/coach.py`](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/py/coach.py)
  — selects boards into per-chunk packets, splices the subagents' prose back into the PBN, validates.

The flow in one line: `coach.py packets` builds packets → one Claude subagent per packet writes
prose per GENERATOR.md → `coach.py splice` writes the curated PBN → it's gated and resolved into
the served files the app reads. The spec files ARE the prompts — point Claude at them.

---

## How to use this draft
David reviews; once approved, deliver to Rick (email / Google Doc / PRs from the fork — TBD).
Part A items can also go as pull requests from `ADavidBailey/Bridge-Classroom`.
