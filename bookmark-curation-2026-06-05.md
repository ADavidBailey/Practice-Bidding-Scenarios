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

5. **Spot-check the fan-out in the trainer**, especially a competitive
   scenario (Basic_Takeout_Double / Basic_Overcall) with Randomly Rotate on —
   rotation + competitive auctions is the newest ground.
6. **Play-stage coaching for the 12 play scenarios** (Finesses, Notrump Play,
   Suit Contract Play). Needs the trainer's per-trick coaching markers
   ([ROLE]/[STAGE]/per-trick anchors) — a real build. This is the next
   frontier.
7. **Trainer `[also-ok]` support**: judgment boards carry defensible
   alternatives; make the quiz score them amber ("defensible") not red ✗.
   Parser + quiz change in server.py/app.js.
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
