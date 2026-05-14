# Bridge Play Trainer — Design Spec

**Date:** 2026-05-14
**Status:** Draft — pre-build

A scenario-based training tool that teaches **card-reading and inference**. The user plays out a deal (declarer, defender, or both); after each trick, Claude evaluates the user's read on the unseen hands and explains its own reasoning.

## Goals

- Train **inference**, not raw card-play. The cards are scaffolding.
- Force the user to **articulate** what they know about each unseen hand.
- Give **graded feedback** — what they got right, what they missed, and why.
- Be **fast to iterate on**: bridge-table UI is the long pole, so MVP defers it.

## Non-goals (for MVP)

- BBO integration (we generate locally; less complexity, no automation fragility).
- Photorealistic bridge-table rendering (text/HTML table is fine).
- Real-time multi-player. Single user, Claude is everyone else.
- Simulating human defensive errors. DDS-based "perfect" defense is the baseline.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Scenario picker (uses existing btn/pbn pipeline output)  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Deal loader: pulls 1 deal + its auction from pbn-rotated │
│ + bba/ output. Rotates so user is in declarer's seat     │
│ (or defender's seat, per mode).                          │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Game state tracker:                                       │
│   - Auction (full, known)                                 │
│   - Cards played per position                             │
│   - Visible hands (user's + dummy, or user only)          │
│   - Current trick / leader                                │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│ Play loop (per trick):                                    │
│   1. Render table state to user                           │
│   2. User plays their card (or types it)                  │
│   3. DDS picks reasonable card for each unseen position   │
│   4. After trick: PROMPT user for E/W estimates           │
│   5. Claude evaluates → grades + explains                 │
│   6. Repeat until 13 tricks                               │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│ End-of-deal summary: contract result, inference scoring   │
│ across all 13 tricks, key lessons.                        │
└──────────────────────────────────────────────────────────┘
```

## Components

### 1. Deal source

Reuse existing pipeline output:
- `pbn-rotated-for-4-players/{scenario}.pbn` — already rotates so each seat has a turn declaring
- `bba/{scenario}.pbn` — has full auction + final contract

Pick a random deal from the chosen scenario. Re-rotate as needed so the user always sits where they want (declarer / dedicated defender / random).

### 2. Defender play engine

Use a **double-dummy solver** (DDS):
- **Choice**: `dds` (Bo Haglund's library) via Python `python-dds` or `endplay` package. Both are well-maintained.
- For each unseen position's turn: DDS computes the optimal card given current state.
- **Layer simple signaling** on top of DDS's choice (attitude on partner's lead, count on declarer's leads). DDS alone doesn't signal — but a deterministic rule like "play HxL → high-low encourages, low-high discourages" can be applied when DDS leaves ties in card selection.

### 3. Claude inference layer

Each trick after play, Claude receives:
- The auction
- Full hand of the user
- Dummy (if user is declarer)
- All cards played so far (with attribution)
- The user's estimate (free-text or structured)

Claude evaluates:
- Is the user's estimate consistent with everything known?
- What's the *correct* current read (Claude's own analysis)?
- Where does the user diverge, and why is each divergence right or wrong?
- One actionable hint: "next trick, watch for ___".

### 4. User-input UI

**Free text mode (early tricks 1–4):**
> User types: "I think W has ♠Kxx, ♥QJxxx, ♦Ax, ♣xxx — about 11 HCP. Their lead of ♥4 looks like 4th-best."

Claude parses prose loosely. No syntax requirements.

**Structured mode (tricks 5+):**
- Per defender: 4 numeric inputs (♠/♥/♦/♣ length) + 1 HCP estimate
- Constraint: lengths sum to remaining cards in each suit; HCP totals reasonable

Why switch? Early on, knowledge is fuzzy and prose captures uncertainty ("maybe singleton ♣"). Later, after multiple tricks of evidence, the player should be locked into a specific read and structure forces precision.

### 5. Grading rubric

Per-trick estimate scoring:

| Category | Full credit | Partial credit | Wrong |
|---|---|---|---|
| Suit length (each suit) | Exact count | ±1 | ±2+ |
| Honor location | Correctly placed | Wrong defender | Missing entirely |
| HCP estimate | Within ±1 | Within ±3 | Off by 4+ |
| Inference quality (prose only) | Reasoning is sound | Reasoning partial | Reasoning flawed/missing |

End-of-deal: aggregate score (% correct across all tricks).

## User-facing modes

- **Play**: User is declarer. Sees own hand + dummy. DDS plays both defenders.
- **Defend**: User is defender (E or W). Sees own hand only. DDS plays declarer + dummy + partner.
- **Both**: User opt-ins to defending OR declaring per deal (alternating? user pick?).

## Scenario integration

The "Pick a scenario..." flow uses our existing button-layout files. Each scenario gives:
- A set of 500 dealer-generated deals
- BBA-computed auctions for each
- A natural HCP/shape distribution (per the scenario's `.btn` constraints)

This means the trainer's hands are pre-curated for educational value — the user practices on, e.g., "Slam after Major Fit" deals or "Weak NT" deals, not random shuffle.

## MVP slice (build first)

To validate the loop before investing in production-quality UI:

1. **Single scenario**, hardcoded path (e.g., `pbn-rotated-for-4-players/Major_Suit_Fit.pbn`).
2. **User is always declarer** (skip Defend/Both for MVP).
3. **Minimal web UI** — single HTML page, basic CSS table of 4 hands + auction + current trick + input box:
   ```
        North (dummy)
        ♠ A 8 6
        ♥ K 7 4 2
        ♦ A K 9
        ♣ Q 5 3

   West  Trick 3:               East
   ♠ Q  W: ♠Q  N: ♠A  E: ♠2     ♠ J
            S: ♠5 ▼

        South (you)
        ♠ K 10 4
        ♥ A Q 8 6 3
        ♦ J 8
        ♣ A K 4
   ```
4. **DDS-driven defenders** via `endplay` (Python).
5. **Free-text estimates only** (skip structured for MVP).
6. **Claude evaluator** in the loop — talks to user, evaluates, explains.

Goal of MVP: prove the per-trick inference loop is engaging and educational. UI/structured mode/defender role can come later.

## Decisions (2026-05-14)

1. **Platform: web app.** Browser frontend (HTML/JS), backend handles DDS + Claude API.
   - MVP: minimal HTML page + a small server (Python FastAPI or similar).
   - Bridge table rendered as HTML/CSS (simple grid of suits/cards; not photorealistic).
2. **DDS library**: deferred — open question. `endplay` is the safest default (pure Python, well-maintained, DDS bindings included). Revisit when starting code.
3. **Signaling: user choice** at session start.
   - Attitude: standard high-encourage / upside-down low-encourage
   - Count: standard hi-lo even / standard lo-hi even (and inverted of each)
   - Suit preference: Lavinthal / McKenney / off
4. **Opening lead: user choice** at session start.
   - Realistic-human heuristic (4th-best from longest/strongest, top of sequence, etc.) — default
   - DDS-optimal (more punishing, exposes too much info)
   - Random-among-reasonable (training mode where the lead doesn't telegraph the layout)

## Still open

- **Where does Claude live?** API calls from the backend per trick. (Default choice, no user controversy.)
- **Score persistence**: skip for MVP; add later if useful.

## Build order suggestion

1. **Pipe 1**: Pick a deal, render text table, walk through 13 tricks with DDS playing everyone (no user input, no Claude). Validates state tracking.
2. **Pipe 2**: User-input layer — user plays declarer's cards.
3. **Pipe 3**: Claude inference layer — after each trick, prompt + evaluate.
4. **Pipe 4**: Free-text → structured handoff at trick 5.
5. **Pipe 5**: Defender mode + Both mode.
6. **Pipe 6**: UI polish (HTML table? VS Code panel?).

Each pipe is testable on its own. Pipe 3 is the value-add — everything before it is plumbing.

## Risks / unknowns

- **DDS pace**: not a concern, DDS is fast (~1ms per solve).
- **DDS realism**: defenders play double-dummy, so they "know" declarer's cards. This is unrealistically good. Layer some "hide info" logic if needed, but MVP should accept it.
- **Claude latency**: ~3–5s per evaluation. For 13 tricks, that's ~1 min of Claude time per deal. Acceptable for a thinking exercise.
- **Free-text parsing**: Claude can interpret loose prose reliably — this isn't a hurdle.
- **Bridge-table rendering**: text/HTML is fine for MVP. Polished UI is post-MVP.

## What we'd need to start

1. **`endplay` installed** (pip install).
2. **Pick a starter scenario** (preferably one with good hand variety).
3. **One sample deal** to walk through manually, to confirm the interaction feels right.
4. **A rough conversation transcript** showing what each trick's prompt+response looks like.

We can do step 3+4 in chat before writing any code — sketch a "play session transcript" by hand, see if it's the experience you want.

## Next step proposal

**Tomorrow**: I sketch a hand-written sample transcript of one full 13-trick session — user as declarer in a specific scenario, with my inference prompts and feedback at each trick. We use that to validate the experience before any code gets written.
