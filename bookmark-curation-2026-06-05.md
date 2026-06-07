# Bookmark — curation status (2026-06-05)

Session ended here. Current state and what's next.

## Where things stand

- **Plan of record:** `pbn-curation-plan.md`. Format reference:
  `bba-curated/README.md` ({Curate} comment block + `py/select.py` filter).
- **Layer A** (DD gate + features): run over all 19 coaching scenarios,
  refreshed after the Basic-Bridge cc fix. Tools: `py/curate.py`
  (resumable, reads the `# curate:` directive in each `.btn`),
  `py/annotate.py`, `py/select.py`, `py/auction_diff.py` (`--base <ref>`
  for diffing against a pre-change commit; run with `python3 -P` —
  select.py shadows stdlib select).
- **Layer B pilot (Basic_NT):** all 500 boards graded. **Re-graded
  2026-06-05 after the `<20` cap regen** (see item 2): 493 deals unchanged
  (deal_hash carry-over), 7 new 18-19 HCP / 6NT boards graded fresh.
  Current: 304 textbook / 116 standard / 57 judgment / 23 reject (bidding).
  Annotated PBN: `bba-curated/Basic_NT.pbn`. Report:
  `bba-curated/Basic_NT-graded-report.md`.
- **Basic-Bridge cc fixed** (Gerber-over-NT off etc.); all 21 dependent
  scenarios' bba/ regenerated and committed (eaa3abe9d by the Claude Code
  session). 83 boards changed; verdict reuse worked (only 22 re-graded).
- **Email to Rick**: draft in Gmail ("Curation step built — first
  results..."), recipient placeholder = David's own address. Links require
  push before sending.

## Open items (in order)

1. **DONE (2026-06-05) — spot-check complete, rubric calibrated.** David
   reviewed 10 boards. One mechanical bug found+fixed (430 wrong leader →
   leader now pre-computed). One calibration ruling: board 137 (South
   passes a 2NT invite on a flat 16) is **judgment + also_ok, not reject** —
   borderline-but-defensible bidding decisions are judgment; reserve reject
   for indefensible calls. Recorded in pbn-curation-plan.md grading criteria.
   The grader is trusted for the fan-out.
2. **DONE (2026-06-05) — Option 1 chosen.** Raised the responder cap to
   `hcp(north) < 20` (`1c1cc7b7d`), re-ran the full pipeline, and re-graded
   Layer B. The 6NT/18+ row now occurs (1.4% of deals; with Gerber off BBA
   raises 1NT straight to 6NT, `1N P 6N`). 7 new boards: 4 textbook /
   3 standard bidding, all `intended`. The 11 old 17-count→6N boards stay
   `reject` (brief wants 17 = 4NT quantitative). All pushed.
3. **DONE (2026-06-05) — fan-out complete: all 19 scenarios curated.**
   Layer B graded every scenario's 500-board pool (5 subagents each,
   leader pre-computed, board-137 calibration applied). Each has a
   `{Curate}`-annotated `bba-curated/<scn>.pbn` + `<scn>-graded.json`.
   `bba-curated/theme-index.json` aggregates declarer/defense themes across
   all scenarios (e.g. count-winners 345 textbook boards, finesse-safe-hand
   289, finesse-basic 157, establish-long-suit 133, hold-up 36, endplay 19)
   — this is what cross-scenario play lessons draw from. Vocabulary extended:
   added `endplay` to the declarer themes (README updated). A few boards per
   scenario carried through unannotated due to genuine duplicate deal_hashes
   in the pools (harmless).
   Scenario-design notes surfaced for later (not blocking): Rabbi's Rule —
   robots run Blackwood to slam on ~60% of boards, diluting the "you already
   have 10 tricks" point; Choice_Of_Finesses / Two_Way / To_Finesse — the
   constraints place the key honor favorably only ~20-35% of the time, so
   the genuine-decision boards are a minority of each pool (still plenty for
   a 30-board lesson). These are constraint-tightening opportunities in the
   `.btn` masters when convenient.
4. **DONE (2026-06-06) — Randomly Rotate + bidding coaching fan-out.**
   - Trainer (AI-Bridge-Play-Trainer): added "Randomly Rotate" — seats the
     student in either bidding seat per board; coaching uses pronoun tokens
     (@S/@s/@Your/@your/@v(base|third), parens not braces) rendered per seat
     by `fill_pronouns`. Only applies to rotation-ready (tokenized) coaching;
     non-tokenized scenarios stay on their authored seat. "Play as" greys out
     while rotation is on (mutually exclusive). Trainer now reads
     `coaching-curated/` first, then `coaching/`, then `bba/`. Also fixed:
     orphaned Continue button during play (post-auction reflection now
     passive).
   - Coaching generator productionized: `coaching-curated/GENERATOR.md` (spec
     incl. the "use @S once per chunk" repetition rule) + `py/coach.py`
     (`packets` / `splice`). Work files in `coaching-curated/.work/`
     (gitignored).
   - Fan-out: all 7 Beginners-Bidding scenarios now have tokenized both-seats
     lessons in `coaching-curated/*.pbn` (Basic_NT + the 6 others), 30 boards
     each, validated (no [BID Pass], no card recitation). The whole Beginners
     Bidding section is curated+coached and live in the trainer.

## Open items (in order)

0. **DONE (2026-06-06) — coaching architecture fix (Option A).** Two bugs
   found while testing: (a) the prose leaked partner's concrete holding
   during the auction ("partner has six spades"); (b) worse, on multi-round
   auctions the trainer's `parse_coaching` DEFERS any prose after a partner
   `[show N]` to the post-auction chunk, which renders first-person — so
   "You have 10 HCP" described partner. Root cause: my both-seats coaching
   used mid-auction `[show]`, which the trainer (built for single-student
   Baker-Bridge coaching) defers. Fix (Option A, David's call): NO `[show]`
   in `[BID]` chunks — only the closing `[show NS]`; describe what each call
   SHOWS by agreement, never the actor's concrete holding. Proven via the
   trainer's own `parse_coaching` (each call renders in the right person).
   All 7 bidding scenarios regenerated, validator-clean, endplay-parse,
   `[ACCEPT]` intact. `py/coach.py validate` now flags any mid-auction
   `[show]` and missing N/S `[BID]` anchors. GENERATOR.md is the Option A
   spec. (Trainer unchanged — no `server.py`/`app.js` edits needed.)

5. **Spot-check the fan-out in the trainer**, especially a competitive
   scenario (Basic_Takeout_Double / Basic_Overcall) with Randomly Rotate on —
   rotation + competitive auctions is the newest ground.
6. **Play-stage coaching for the 12 play scenarios** (Finesses, Notrump Play,
   Suit Contract Play). Needs the trainer's per-trick coaching markers
   ([ROLE]/[STAGE]/per-trick anchors) — a real build. This is the next
   frontier.
7. **`[ACCEPT]` / judgment-alternative support — PARTLY DONE (2026-06-06).**
   Finding: the trainer ALREADY supports `[ACCEPT <call>]` (parser
   `_extract_accept`, per-quizzed-call quiz scoring — picks the alternative →
   green "either X or Y is fine"). No trainer work needed. The gap was the
   generated coaching: (a) it didn't emit `[ACCEPT]`, and (b) ~45 boards
   narrate one N/S call without its own `[BID]` anchor (Basic_NT responses,
   Basic_Major openings), so rotation can't quiz that call and `[ACCEPT]`
   can't attach. Pass-judgments (declines) can't anchor at all — prose only.
   Done: `GENERATOR.md` now documents `[ACCEPT]` + the structure discipline
   (one `[BID]` per N/S non-pass call, framing-only intro); `py/coach.py`
   gained `validate` (gates `splice`); **Basic_NT regenerated clean** (0
   structure issues, `[ACCEPT]` on b13/b38/b46, endplay-parses).
   **DONE (2026-06-06):** all 7 bidding scenarios structure-tighten regen'd —
   `coach.py validate` reports 0 issues for every one, all endplay-parse, and
   `[ACCEPT]` markers are on the non-pass judgment boards (Basic_NT,
   Basic_Major, Basic_Weak_2). Pass-judgment declines stay prose-only (can't
   anchor `[BID Pass]`) — a known, acceptable limitation. Also removed a stray
   `coaching-curated/Basic_NT-input.pbn` (pilot leftover that the menu would
   have shown as a bogus scenario). The whole Beginners Bidding section is now
   curated + coached + rotation-ready + judgment-aware.
8. **Scenario-design follow-ups** (non-blocking): Rabbi's Rule Blackwood
   dilution; finesse scenarios' favorable-honor placement. Constraint
   tightening in the `.btn` masters when convenient.

## Session conventions

- Cowork sandbox: endplay installed via
  `pip install endplay --break-system-packages`; long runs must be
  time-budgeted (`CURATE_BUDGET`) — background processes don't survive
  between bash calls.
- Commits from Cowork: `git -c user.name="David Bailey"
  -c user.email="adavidbailey@gmail.com" commit ...`. **No push from
  Cowork** (no credentials, by David's choice) — David pushes from
  Terminal/Claude Code.

## Claude Code session note (2026-06-05, late)

- Regrade lists for **all 21** Basic-Bridge scenarios are pre-generated in
  `bba-curated/.progress/<scn>-regrade.json` (git-ignored), via
  `python3 -P py/auction_diff.py --base 89a22f775 <scns>` (baseline
  `89a22f775` = the pre-card-change parent). 83 boards changed total. The
  Layer B fan-out (open item 3) can read these directly — no need to
  re-diff. Details: `bba-curated/.progress/_README_baseline.md`.
- Working tree clean. **Pushed to `origin/main` (David approved)** —
  `fcc909014` + `77e499617` + the bookmark commit are now on origin; local
  and origin in sync. Rick-email links now resolve.

## Claude Code session note (2026-06-07) — Play-Trainer feedback

The trainer's new in-app feedback button (🚩 Report → GitHub issues in
AI-Bridge-Play-Trainer) surfaced two coaching items for **Basic_What_To_Open**:

- **Board 13 prose (issue #13) — DONE, committed + pushed (`2eb62ee19`).**
  The 4S `[BID]` chunk called North's `AKT65432` "a strong fit for partner's
  spades"; now "a self-sufficient spade suit" (a long, solid suit is its own
  trump source, not support for partner). Worth confirming GENERATOR.md's
  terminology rules keep this so a regen doesn't reintroduce "fit for partner".
- **Count-your-tricks request (issues #8/#9 — left OPEN as a tracker).** When
  a student plays a *bidding* scenario out as declarer, they want the
  "count your sure winners" prompt. Decision (David): do NOT hand-author a
  one-off tip — instead **fold Basic_What_To_Open (and likely the other
  bidding scenarios) into the play-coaching generator's scope** (open item 6 /
  `GENERATOR-PLAY.md`): run `play_splice` on it once the play generator lands,
  so declarers get the same analyzed `[ROLE declarer][STAGE auction-end]`
  count-the-winners directive as the 12 dedicated play scenarios.

Second round (issues #15/#16, board 15 of Basic_What_To_Open — South
`A762.QJT2.A965.A`, a 4-4-4-1 opening 1♦ into `1♦-2♣-2♥-2N-3N`):

- **Board 15 prose (#15) — DONE, committed (`68cd947fd`).** The intro
  mislabeled South's 4=4=4=1 as "a strong balanced opening, just shy of 1NT";
  reworded to a three-suiter (a singleton rules out 1NT). **Generator guard
  for GENERATOR.md:** never call a hand with a singleton/void "balanced"
  (the prose also reaches for "balanced-looking" elsewhere) — same spirit as
  the #13 terminology rule.
- **Board 15 re-curation candidate (#16 — left OPEN as tracker).** The 2♥
  rebid is reverse-*shaped* yet South has only 4 diamonds / 15 HCP. It's fine
  in 2/1 GF (2♣ already forced game, so 2♥ isn't a true reverse), but for a
  *Basic* "what to open" lesson the 2/1 sequence with a reverse-looking rebid
  is confusing. Decision (David): **flag board 15 for re-curation** — prefer
  replacing/dropping it over patching prose. A curation note for whoever
  reselects the 30 boards: avoid openings whose follow-up auction needs 2/1
  machinery to read correctly.

---

## 2026-06-07 — Hold_Up_3N scenario bug found via play-coaching pilot

Starting the **play-stage coaching** pilot (Hold_Up_3N, theme=hold-up) surfaced
a scenario-design bug, not a coaching bug.

**Symptom.** Of 12 pilot boards, the play-coaching subagents found only 1 that
was even arguably a hold-up on the *real* opening lead, and on inspection that
one (board 17, ♠AK opposite ♠QJ doubleton) isn't a true hold-up either — you
just cash both top spades.

**Root cause.** The old `Hold_Up_3N.btn` put the long heart suit in **East**
(`predeal east HKQ`, `hearts(east) > 4`). But South declares 3NT, so the
opening leader is **West**, who was short in hearts and led their *own* long
suit. The heart hold-up the scenario teaches almost never arose. Evidence: the
corrected lead-driven oracle over the full 500-board `bba/Hold_Up_3N.pbn` pool
found West leads a heart on only **22/500** boards and a DD-necessary hold-up on
only **4/500 (0.8%)**.

**Two fixes landed (PBS-side, uncommitted):**

1. `py/curate.py` `holdup_required` rewritten to be **lead-driven**: it now
   computes West's actual standard opening lead (4th-best of the longest,
   strongest suit; top of a 3-honor sequence) and tests whether *winning the
   first round of the led suit* costs the contract. Stopper-count agnostic
   (catches two-stopper "duck once to strand the short hand" as well as classic
   Axx). New helpers `opening_lead_vs_nt`, `_honor_sequence_top`.

2. `btn/Hold_Up_3N.btn` rewritten so **WEST** holds the long suit and leads it:
   `predeal west HKQ`, `hearts(west) > 4`, `hcp(west) < 8` (so no outside
   entry); South keeps one stopper (`predeal south HA`, `hearts(south) < 4`);
   East short hearts (`hearts(east) < 4`) and, as the stronger defender, holds
   the side entry to knock out. @chat prose updated to the corrected geometry
   (duck to exhaust **East**, the entry hand; West's length is stranded).

**Verification.** Monte-Carlo over deals matching the new constraints: **13% of
makeable boards are DD-necessary hold-ups** (vs 0.8% before, ~16x). A 500-board
run should yield 50+ clean hold-up boards.

**Open / next:**
- The pilot play-coach JSONs in `coaching-curated/.work/Hold_Up_3N-play-*` were
  generated off the BROKEN pool — discard; regenerate after the pipeline re-run.
- **David to re-run the pipeline for Hold_Up_3N** (bba needs the Windows VM):
  `dlr → pbn → rotate → bba → curate` (e.g. from build-scripts-mac:
  `python3 pbs-pipeline-mac.py Hold_Up_3N "dlr+"`). Then grade + play-coach.
- Same class of bug may affect the other **avoidance** play scenarios
  (Choice_Of_Finesses, Two_Way_Finesse, To_Finesse_Or_Not_To_Finesse): confirm
  the suit/entry that the lesson hinges on sits with the hand that the *real*
  opening lead and play actually route through. Worth an oracle/lead pass on
  each before generating their play coaching.

### Same-bug sweep of the avoidance/finesse play scenarios (2026-06-07)

Checked the other `oracle=shape` play scenarios for the same leader-seat bug
(danger suit in the wrong defender). West's opening-lead suit over each
500-board `bba/` pool:

- **Choice_Of_Finesses — SAME BUG, fixed.** West led a heart 0/500; East held
  the 5+ hearts on all 500. Rewrote `btn/Choice_Of_Finesses.btn`: long hearts
  + the SQ to **West** (so the SPADE finesse loses to the danger hand = fatal);
  CQ falls to East by elimination (so the CLUB finesse is safe); South keeps
  one heart stopper and ducks to exhaust East. Labels flipped vs the old prose
  (now: take clubs, avoid spades). MC verify: West leads a heart 59/60, 3NT
  makes DD 57/60. Needs the same pipeline re-run as Hold_Up_3N.
- **To_Finesse_Or_Not_To_Finesse — no seat bug, prose softened.** Suit contract
  (4S); the club finesse itself puts East on lead, so East-as-danger doesn't
  depend on the lead. But in a trump contract East cashes ≤1 heart before a
  ruff, so "East cashes a 5-card suit" oversold it. Reworded @chat to lead with
  count-your-tricks / no-upside; kept the heart danger as a footnote. No regen.
- **Two_Way_Finesse — structurally fine.** Pure two-way guess for the QD,
  hearts split evenly (W60/E66). Added a `# curate-note:` to the .btn: TIER by
  readability (prefer boards where an inference points one way), de-prioritise
  true 50/50s. (Parser-safe: `curate_directive` matches only `# curate:`.)

Net: two .btn redesigns (Hold_Up_3N, Choice_Of_Finesses) need David to re-run
`dlr+` through the pipeline (bba on the Windows VM); To_Finesse + Two_Way are
prose/curation-note only. All uncommitted.

### Hold_Up_3N play-coaching pilot + trick-map verification (2026-06-07)

Built the first play-stage coaching pilot on the redesigned Hold_Up_3N pool
(12 boards) and, in doing so, added a verification layer that the play
pipeline needs.

- **Layer A re-run** on the corrected pools (had to clear stale Jun-5
  `.progress` + JSON — resume is keyed by board ORDER, not deal hash): 63
  DD-necessary hold-ups / 500 (Hold_Up_3N), 500/500 avoidance-shaped (Choice).
- **Oracle-derived graded.json** for both (declarer discipline): holdup_required
  -> textbook hold-up; ok+avoidance_shaped -> textbook avoidance. Re-annotated
  bba-curated PBNs so deal_hashes match the new pool.
- **NEW `py/suit_tricks.py`** — exact single-suit double-dummy with known cards
  (seat-aware, positional finesses). `coach.py play-packets` now injects a
  verified `trick_map` (top / establishable per suit + development_suit) and the
  authoritative `opening_lead` into every packet, so the generating subagent
  NARRATES counts and the lead instead of computing them — that was the failure
  mode (board 1 first drafted "four spades" for a 3-trick suit and missed clubs
  as the real source). Fixed a `top_tricks` overcount on long 5-5 fits.
- **`play-splice` now cross-checks** the spliced pre-lead card against the
  computed standard NT lead (caught a HK-from-KQxxx slip; correct is 4th-best).
- Verified with the trainer's OWN `_strip_post_auction_blocks` + `parse_tips`
  (endplay parses, 4 tips per board, suit symbols render). All 12 boards
  reconcile to 9 tricks; all leads validated. `coaching-curated/Hold_Up_3N.pbn`.

Open: delete the now-shadowed hand-authored `coaching/Hold_Up_3N.pbn` (30
boards, broken under the redesign; trainer prefers coaching-curated/). Choice
play coaching not yet generated (graded.json ready). Other play scenarios
await fan-out through the same trick-map-grounded pipeline.
