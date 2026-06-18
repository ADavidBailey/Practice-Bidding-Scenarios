> **STATUS: DRAFT — NOT YET IN EFFECT.**
> This is a proposed charter for review by David and Rick. It is **not** the active
> coordination contract and must **not** be acted on by either agent until David
> adopts it (see "How this becomes active" at the bottom). To activate, David
> renames this file to `coordination/README.md` and commits it. Until then, the
> only authoritative description of the workflow is whatever the two agents have
> already been doing in `PBS-*.md` / `TR-*.md`.

# Cross-Repo Coordination Charter (PROPOSED)

**Repos:** Practice-Bidding-Scenarios (PBS, *content + pipeline*) and
AI-Bridge-Play-Trainer (Trainer, *engine + UI*).
**Purpose:** let the two Claude agents collaborate **without a live connection and
without David relaying messages**, while keeping David in control of every decision
that actually matters.

---

## 0. Why this exists

Claude Code running in one repo cannot talk to Claude Code running in another. So the
two agents communicate **asynchronously through files** in this `coordination/`
folder, which lives in the PBS repo and is reachable by Trainer through
`BRIDGE_DATA_ROOT`. This folder is **meta/shared** — a Trainer *write here* is
coordination, not engine data, so it does **not** violate the "runtime never writes
the data path" invariant.

---

## 1. The message pipe

- **One file per message** so the two agents never clobber each other:
  `PBS-NNNN.md` (from PBS) and `TR-NNNN.md` (from Trainer), zero-padded so they sort
  in order (`PBS-0008.md`, `TR-0008.md`).
- **Each message has:**
  - a header — `PBS-N · in reply to TR-M` (or `(new thread)`),
  - **From / Date / Re:** lines,
  - the body, and
  - a final **`STATUS:` line** — one of `awaiting TR`, `awaiting PBS`, `needs David`,
    or `idle`.
- **`LOG.md`** is append-only, **one line per message** (`PBS-8 · awaiting TR ·
  promoted Choice_Of_Finesses`), so David can skim the whole conversation without
  opening files.
- **Bulk data handoffs** (candidate sets, gate verdicts) stay in
  `coaching-curated/.work/<scenario>-*.json`; messages reference them **by path**,
  they are never pasted inline.

### Numbering rule (prevents collisions)

Each agent numbers **only its own prefix**, taking `max(existing of my prefix) + 1`.
The two sequences are independent (`PBS-8` and `TR-8` can both exist). An agent never
reuses or back-fills a number. If two same-prefix files ever collide, the one with the
later file timestamp renames itself to the next free number and fixes its `LOG.md`
line.

---

## 2. Turn-taking and triggering

- Whoever wakes **reads every message after the last one it processed**, acts, writes
  its reply + `STATUS:`, appends to `LOG.md`, and **stops**.
- The `STATUS:` of the latest message says whose turn it is. `awaiting TR` → Trainer
  acts next; `awaiting PBS` → PBS acts next; `needs David` → **both park**; `idle` →
  thread is at rest.
- **David is the clock, never the courier.** MVP triggering is manual: David tells
  whichever agent he wants to advance **"check coord"**; it processes and stops. (A
  hook to auto-wake the other agent is possible later; start manual.)

---

## 3. Rules of engagement (the part that needs David's judgment)

### An agent MAY do alone
*(mechanical, gated, reversible, and within bias-to-drop):*
run the gate; run the pre-screen; author coaching prose for candidate boards; splice;
run the consumer; **promote a scenario that PASSES the gate**; run the de-risk
measurement; write coordination messages.

### An agent MUST park with `needs David`
content **judgment** calls (e.g. "is this a good teaching board?"); scope or order
changes; **any push to `main`**; deleting or overwriting David's work; large token
spend (e.g. the 300+ board scale-up); or **anything crossing the content↔engine
line**.

### Stop condition
A thread that bounces ~3 times without converging, or that hits any "must park" item,
**parks itself with `needs David`**. No infinite ping-pong. A per-turn work cap keeps
either agent from running away.

---

## 4. The content↔engine line (who owns what)

- **PBS owns content:** the hands, the coaching prose, what each board teaches, menu
  membership, the pipeline. All coaching `.pbn` editing happens **only in PBS**, in
  `coaching-curated/` (staging), promoted to `coaching/` (served) through the gate.
- **Trainer owns the engine/UI:** card play, scoring, rotation, endpoints, the
  coaching-marker parser. It **reads** PBS content via `BRIDGE_DATA_ROOT` and
  **never writes it back**.
- **The gate is read-only.** Trainer's `verify_play_coaching.py` validates PBS content
  but only writes `.work/<scn>-*-verdict.json` sidecars (and only under
  `--write-verdicts`). It never writes `coaching/` or `coaching-curated/`.

### Content-file ownership rule (the integrity fix)
**Only PBS writes coaching `.pbn` files.** Trainer must never write `coaching/` or
`coaching-curated/`. Before every commit that includes a content file, the committing
agent **diffs staged-vs-working** to catch any concurrent reversion (this rule exists
because an unidentified process once reverted `coaching-curated/Choice_Of_Finesses.pbn`
between `git status` and `git add`).

---

## 5. The two non-negotiables

1. **No keys.** The Trainer must never make an outbound call to any AI service at
   runtime — all coaching is precomputed upstream in PBS. Our users are seniors who
   should never need (or pay for) an API key.
2. **No wrong coaching (bias-to-drop).** We coach an audience that will not report
   errors. When a piece of coaching cannot be **deterministically verified**, the rule
   is **drop it, don't guess.** A missing decision is harmless; a confidently wrong one
   is not.

---

## 6. Autonomy level (David sets this)

Start **tight**: agents may do only the mechanical/gated set above. Run **one** full
loop through the pipe with David watching. Loosen only after he's seen the agents
behave. The mechanical path is already safe via bias-to-drop; the real risk is
judgment/scope, which stays with David until trust is earned.

`CURRENT AUTONOMY LEVEL: ____` *(David fills in: TIGHT / LOOSENED — and the date)*

---

## How this becomes active

1. David and Rick review and edit this file (Section 3 and 6 are the ones to weigh in
   on).
2. The Trainer agent records its agreement (a `TR-*.md` message, or a parallel
   `TR-proposal.md`) so the charter is **jointly owned**, not one-sided.
3. David renames this file `PROPOSED-charter.md` → `README.md`, creates an empty
   `LOG.md`, and commits. From that commit on, the charter is in effect.
