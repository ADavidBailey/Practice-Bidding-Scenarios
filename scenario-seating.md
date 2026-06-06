# Scenario seating — where to put the student

Design rule for which seat the student occupies in a bidding scenario, so the
trainer quizzes the *interesting* decisions. From Rick Wilson (who deploys the
trainer), 2026-06-06, confirming + refining the Basic_NT_Response pilot.

## How the quiz works (Rick)

The quiz hands the first set of questions to **the first seat that has a real
choice**, then alternates between the two partners, bouncing back and forth as
the auction develops. For a 1NT auction it skips the (forced) opening and
starts at the response.

## The rule

**Short auctions** — opener bids, partner responds, opener passes (e.g. 1NT
openings, weak-two openings, simple single-raise sequences): place the student
in the **choices seat** (the responder). One scenario, student = South =
responder. This is the `Basic_NT_Response` pattern: North holds the fixed
opener, South holds the variable hand that makes the real decision.

**Longer auctions** — 2/1 sequences, new-suit responses with rebids, anything
that bounces back and forth (e.g. opening 1 of a major/minor and continuing):
**alternate the opener between North and South** so the student (always South)
experiences both roles as the auction progresses — opening + rebidding on some
boards, responding + inviting on others. One scenario, not two.

## Two ways to get "both seats" — and which to use

There are two mechanisms for putting the student in both seats:

1. **Rotation at play/upload time (preferred for longer auctions).** A 180°
   rotation spins the whole deal so the student (always South) holds what was
   North's hand on the rotated copy — i.e. opener on one copy, responder on
   the other. This is a checkbox/setting, not new content:
   - BBO Practice Table: **"Randomly Rotate"** checkbox.
   - PBS VS Code extension: the **↕ (double-headed arrow) toggle** in the
     button grid, next to Start Bidding Table / Start Teaching Table /
     Auction Compare.
   - pbs-deal-archive-uploader: the rotation radio (**2** = 180°, 4 = 90°).
   - AI-Bridge-Play-Trainer: rotates internally; coaching is stored in real
     compass and mapped by `rotation_shift`, so coached prose follows the
     rotation correctly.
   Rotation reuses the existing curated/coached deals — no new pipeline run.

2. **Dealer-code alternation (only when you need it baked into one PBN).**
   A disjunction over which side holds the opener (below) produces a single
   pool whose *boards* already mix the seating. Use this only when the deals
   must travel as one static file with mixed seats and you can't rely on the
   play environment's rotation. (Pilot: `Basic_Major_Both.btn`.)

**Rule of thumb:** longer auctions → keep the single scenario and turn on
rotation (mechanism 1). Short auctions → rotation is wrong (it seats the
student in the no-decision opener seat half the time), so use the Response
mirror instead. Dealer-code alternation (mechanism 2) is a fallback, rarely
needed.

## Implementing "alternate opener" in dealer code (fallback)

Make the deal condition a disjunction over which side holds the opener shape:

```
# opener-shape / responder-shape predicates for each seat
sOpen = <opener constraints on south>
nOpen = <opener constraints on north>
sResp = <responder constraints on south>
nResp = <responder constraints on north>

# either South opens (North responds) or North opens (South responds)
(sOpen and nResp) or (nOpen and sResp)
```

Roughly half the produced deals seat the opener on each side, so the student
sees both. BBA bids from the hands, so the auctions come out correct either
way. (Keep E/W weak as before so the auction stays uncontested unless the
scenario is about competition.)

## Status of the current bidding scenarios

| Scenario | auction length | seating to use |
|---|---|---|
| Basic_NT | short | responder mirror → **Basic_NT_Response (done)** |
| Basic_Weak_2 | short, but opening IS a judgment call | student = opener stays valid (like What_To_Open); a Response mirror is an *optional additional* lesson, not a fix |
| Basic_What_To_Open | n/a — the *opening* IS the decision | student = opener (current, correct) |
| Basic_Major | longer (rebids) | keep single scenario + **rotation** (mechanism 1) |
| Basic_Minor | longer (rebids) | keep single scenario + **rotation** (mechanism 1) |
| Basic_Overcall | competitive | rotation, or seat student in overcalling side (review) |
| Basic_Takeout_Double | competitive | rotation, or seat student in doubling side (review) |

`Basic_Major_Both.btn` is a built pilot of the dealer-code alternation
(mechanism 2); now that rotation covers the longer-auction case more cheaply,
it's kept only as a comparison and may be retired in favor of
`Basic_Major` + rotation.

`Basic_What_To_Open` is the exception that proves the rule: when the decision
under test is the opening bid itself, the student belongs in the opener's seat
and no re-seating is wanted.

## Note

The play scenarios (declarer/defense) already sit the student where the stream
of decisions is (declaring South), so this rule is a bidding-scenario concern
only.
