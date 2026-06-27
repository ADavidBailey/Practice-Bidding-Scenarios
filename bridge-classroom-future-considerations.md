# Bridge Classroom — Future Considerations (DEFERRED)

**David's directive (2026-06-27): keep changes to Bridge Classroom (the app / fork
engine) MINIMAL for now.** Work within what BC already does. Accumulate engine ideas
here to weigh later instead of building them now. The coaching **content** — PBS decks,
prose, board selection — is the active work and needs no BC changes.

Keep it straight: **engine = the BC fork** (`~/Bridge-Classroom`); **content = PBS**.

## Parking lot — engine ideas to weigh later (not scheduled)

1. **Per-card wrong feedback (3-tier).** Today a wrong lead says the same thing no matter
   which card you picked. Respond to the *actual* choice — correct (terse nod) / reasonable
   ("good thought, but…") / wrong (full why) — with length fading by correctness.
   *Raised 2026-06-27 reviewing Major-LHO. See `project_coaching_feedback_fade`.*

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

## How to use this file
Add new BC engine wishes here as they come up. Nothing here gets built until David
explicitly moves it out of the parking lot.
