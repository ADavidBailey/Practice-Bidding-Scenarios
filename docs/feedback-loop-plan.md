# Plan — Build the feedback → issue → process loop (the linchpin)

## Context — why this matters

Reviewing the existing coaching corpus and getting it learner-ready is a huge job — too big to read board-by-board. It scales through a feedback loop: experienced bridge players (and later learners worldwide) try Bridge Classroom, flag bad boards, and those reports drive collective fixes. We can't recruit that help until the loop is running — so the loop is the linchpin.

Key decision: rather than wait on Rick (busy) to add the Report button, David stands up his own copy of Bridge Classroom and adds the button himself. That makes the full loop runnable now — button → PBS issue → /issue processor — with no dependency on Rick. Rick can adopt the button upstream later, or not.

Everything hangs off one source of truth: coaching-curated. Bridge Classroom (David's copy and Rick's) reads coaching-non-rotated from GitHub main; the Play Trainer reads coaching locally. At world scale you can't fix one deal at a time, so the processor is batch-first: cluster reports by defect class and fix at the class level (gate + corpus sweep + regenerate / drop), not board-by-board.

## Deliverable 1 — the /issue batch processor (built)

A skill at .claude/skills/issue/SKILL.md. On /issue:

1. Pull open classroom-feedback issues from the PBS repo.
2. Cluster by defect class (spoiler · backwards-vs-result · factual error · unknowable claim · marker leak) and by scenario; dedupe duplicates of one root cause.
3. Weight by reporter tier: a learner's "I'm confused" is a clarity signal; an experienced reviewer's "this is wrong" is near a ruling (still verify, but lean toward it).
4. Locate the board by its PBN deal string, never by deal number or board tag — those drift.
5. Verify independently (double-dummy / the convention card) — reports are untrusted until checked.
6. Fix at the right altitude: class-wide → a gate plus a corpus sweep; a single board → patch or drop; an engine/UI bug → forward to the Classroom repo; a bridge-judgment call → consult Rick; no defect → kind reply.
7. Approval gate: triage, verify, and draft on our own, but stop for David's OK before anything leaves the machine. Single-source means a fix is global.
8. Content-fix pipeline: edit coaching-curated → gates → nonrotate.py and bridge_classroom.py → commit + push. Reply in plain language; close the whole cluster.

## Deliverable 2 — David's copy of Bridge Classroom + the Report button (separate repo; engine)

- Fork or clone Rick's Bridge-Classroom repo (Vue 3 + Vite frontend, Rust/Axum + SQLite backend). This work happens there, not in PBS.
- Add a "Report a Problem" modal (free text + Enter) → POST /api/report → creates a GitHub issue in the PBS repo, label classroom-feedback, carrying the payload (scenario, PBN deal, deal number + tags, seat, auction, contract, step, main commit SHA, reporter tier, free text).
- Auth: a GitHub token scoped to Issues-write on PBS, from an env var; degrade gracefully if it isn't set.
- Run it locally for David's own testing now. Hosting for other recruited testers is a later step (or where Rick's upstream adoption comes in).

## Deliverable 3 — interim file-on-report (until the button ships)

David reports a problem in chat; Claude looks up the deal, shows David the issue, and files it (label classroom-feedback). This seeds the processor now and stays on as a quick fallback.

## Status (2026-06-23)

- The /issue processor is built and proven end-to-end on a real (seeded) batch: three reports on Basic_Weak_2 → clustered → verified → fixed → pushed → closed.
- A corpus-wide marker-leak fix shipped: bridge_classroom.py now strips trainer-only [ACCEPT] markers from the served copy, and a sweep cleaned 12 lessons (most of them never reported).
- Still open: David's copy of Classroom + the Report button; an optional gate that auto-catches a reflection contradicting its own result.
