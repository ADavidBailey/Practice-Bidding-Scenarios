# Bridge Classroom — Change requests for Rick

> **STATUS: IN PROGRESS.** Draft on David's machine — **not yet sent to Rick.** We'll send
> Rick an in-the-loop message at a stopping point. Nothing here has been merged into Rick's
> upstream; "built" means committed/pushed to **David's fork only**.

*Draft for David to review before anything goes to Rick. Self-contained: written to be
read cold, without PBS-internal context.*

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

### B3. ENHANCEMENT — per-card (lead/play) 3-tier feedback  *(medium)*
The **bid** version is built (A3, on the fork). Requested: the same fade for **card**
decisions (opening leads and third-hand play). Today a wrong card shows the same text regardless of which card
was chosen. Respond to the *actual* choice — correct (terse nod) / reasonable ("good thought,
but…") / wrong (full why) — with length fading by correctness.

### B4. ENHANCEMENT — full defender play-out with revert-and-correct  *(large)*
Let the student defend the **whole** hand card-by-card (not just the opening lead). A mis-play
is reverted and the correct card substituted, then play continues — the declarer-play model
applied to a defender (South).
- **Status:** prototype + build-ready handoff spec already on our fork, branch
  `defender-playout-investigation` (commits `d753cab`, `23be662`, `aa9c9a5`). Ready to build
  when chosen.

### B5. NICETY — remember the previous attempt on revisit  *(small; optional)*
Returning to a completed deal resets it to the start (a clean re-try) — fine as-is. Optional
improvement: remember the previous lead/play + result instead of fully resetting.

### B6. FIX — affirmation verb on lead lessons  *(tiny)*
On a lead/defense lesson the success cheer can read with bid wording ("Beautifully bid!").
Use the verb that matches the lesson type ("Well led!").

---

## How to use this draft
David reviews; once approved, deliver to Rick (email / Google Doc / PRs from the fork — TBD).
Part A items can also go as pull requests from `ADavidBailey/Bridge-Classroom`.
