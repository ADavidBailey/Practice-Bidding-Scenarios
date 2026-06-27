# Bridge Classroom — Changes (completed & proposed)

Running log of changes to the **Bridge Classroom app/engine** (the fork at
`~/Bridge-Classroom`). Scope here is the **engine/app**. Coaching **content** —
PBS decks, prose, board selection — is tracked in PBS git history, **not** here.
Keep it straight: **engine = the BC fork**; **content = PBS**.

**David's directive (2026-06-27): keep BC engine changes MINIMAL for now.** Work
within what BC already does. New engine ideas accumulate in the parking lot below
to weigh later instead of being built now.

> **Rick-facing version:** the precise, cold-readable change requests for Rick live in
> [`bridge-classroom-requests-for-rick.md`](bridge-classroom-requests-for-rick.md)
> (Part A = built-on-fork → merge; Part B = build/fix). Keep the two in sync.

---

## Completed (built on David's fork — NOT yet merged upstream)

*Verified 2026-06-27 against `~/Bridge-Classroom`: all on `main`, **18 commits ahead of
Rick's `origin/main`**, and pushed to David's `fork/main`. "Built" = committed/pushed to
**David's fork only** — not in Rick's upstream, not in any prod Rick runs. Fork-only
until/unless PR'd to Rick.*

- **Report-a-Problem button.** `ReportProblemModal.vue` + `useReportProblem.js`; endpoint
  configurable via `VITE_REPORT_URL`. Has a real **Rust API route**
  (`bridge-classroom-api/src/routes/reports.rs`) *and* works against the local report-relay
  (the relay + `.env.local` are the gitignored, local-only pieces). Button sits beside the
  bidding box; popup is draggable. Issues land as `classroom-feedback` in PBS → `/issue` flow.
- **Scenario @chat popup.** `ScenarioChatPopup.vue` — sizable, movable popup showing the
  scenario's chat/teaching blurb; shown in Bidding Practice **and** coaching lessons; reopen
  button labeled "Description".
- **Coaching-feedback fade (BIDS).** Three-mode bid feedback: correct call → brief *varied*
  affirmation + the partner/opponent follow; wrong call → full explanation; reads the `⟦ ⟧`
  the generator wraps around the student's justification. Adds a **board-level cheer**
  (Bravo!/Perfect!) when every call on a board was right. *This is the bid analog of proposed
  item 1; the per-CARD (lead/play) version is still open.*
- **Coaching layout.** Left-align the table during practice with the chat open on the right;
  re-center on close; cap coaching-text height to the window so the bid box stays in view.
- **Local-run launcher.** *(Local dev convenience, not a fork commit.)* Desktop
  `Bridge Classroom.command` → Vite dev server + report-relay, opens to the David Bailey
  Scenarios page.

---

## Proposed / parking lot (not scheduled — nothing here is built until David moves it out)

1. **Per-card wrong feedback (3-tier).** Today a wrong lead says the same thing no matter
   which card you picked. Respond to the *actual* choice — correct (terse nod) / reasonable
   ("good thought, but…") / wrong (full why) — with length fading by correctness.
   *Raised 2026-06-27 reviewing Major-LHO. See `project_coaching_feedback_fade`.*
   **Note:** the **bid** version of this fade is already built on the fork (see Completed →
   Coaching-feedback fade). This item is the still-open **per-card (lead/play)** analog.

2. **Full defender play-out with revert-and-correct.** Let the student defend the WHOLE
   hand card-by-card (not just the opening lead); a mis-play is reverted and the correct
   card substituted, then play continues — the declarer-play model applied to a defender
   (South). *Cowork produced a build-ready handoff spec on branch
   `defender-playout-investigation` in `~/Bridge-Classroom` — ready to build when chosen.*

3. **Revisit state (NOT a bug).** Returning to a completed deal RESETS it to the start —
   your hand shown, ready to lead again: a clean re-try. Reasonable as-is. FUTURE nicety:
   optionally *remember* the previous lead + result instead of resetting. *Confirmed
   behavior 2026-06-27 (David).*

4. **Cosmetic affirmation verb.** On a lead lesson BC says "Beautifully bid!" — should read
   "Well led!" (correct verb per lesson type).

5. **`[showcards]` multi-seat parser bug.** *(Found 2026-06-27.)* A tag naming two seats —
   `[showcards N:C4, E:CT]`, or the documented `E:S7,S:S5` form — is mis-parsed: the seat
   regex in `src/utils/pbnParser.js` (the `([NESW]):([^,\s]+(?:,[^,\s]+)*)` pattern, ~line
   342) greedily swallows `,E:CT` as a *second card of North*, so the second seat is lost.
   **Worked around in content** by putting a **space after the comma** (`N:C4, E:CT`), which
   breaks the greedy match. A proper one-line regex fix would make the documented multi-seat
   format work without the space. *Surfaced while making dummy "play" its card in the
   third-hand RHO defense sets.*

6. **Header title/greeting overlap (CSS).** *(Found 2026-06-27.)* On a long collection title
   (e.g. "…Bailey Scenarios - Third Hand vs Notrump") the title overprints the
   "Welcome back, David" greeting — the two render on top of each other. The title doesn't
   truncate or wrap before the greeting. Cosmetic only; fix with ellipsis-truncation or
   allowing the title to wrap. Affects any long title.

---

## How to use this file

Add new BC engine changes here — **Completed** when shipped, **Proposed** when raised.
Nothing in the parking lot gets built until David explicitly moves it out.
