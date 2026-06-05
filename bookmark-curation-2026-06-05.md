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
- **Layer B pilot (Basic_NT):** all 500 boards graded; 22 re-graded after
  the cc fix. Current: 306 textbook / 114 standard / 57 judgment / 23
  reject (bidding). Annotated PBN: `bba-curated/Basic_NT.pbn`. Report with
  10 spot-check boards: `bba-curated/Basic_NT-graded-report.md`.
- **Basic-Bridge cc fixed** (Gerber-over-NT off etc.); all 21 dependent
  scenarios' bba/ regenerated and committed (eaa3abe9d by the Claude Code
  session). 83 boards changed; verdict reuse worked (only 22 re-graded).
- **Email to Rick**: draft in Gmail ("Curation step built — first
  results..."), recipient placeholder = David's own address. Links require
  push before sending.

## Open items (in order)

1. **David: finish the spot-check** of the 10 boards in
   `Basic_NT-graded-report.md` (board 430 already caught a grader error —
   wrong opening leader; rubric fixed: leader is now pre-computed in the
   grading packets). Each disagreement hardens the rubric.
2. **David: decide the Basic_NT 6NT question.** The `.btn` caps responder
   at `hcp(north) < 18`, so the brief's "6NT = 18+" row can never occur;
   BBA bids 6N on 17s → 11 rejects. Option 1: raise cap to <20 and re-run
   the full pipeline + re-grade Basic_NT (new deals). Option 2 (lean):
   drop the 6NT row from this beginner brief; slam gets its own scenario.
3. **Fan out Layer B** to the other 18 scenarios once the rubric is
   calibrated (5 parallel subagents per scenario, ~100 boards each; add
   the pre-computed `opening_leader` field as in the regrade packets).
4. Then: theme index across scenarios, re-point the coaching generator at
   curated selections, trainer `[also-ok]` support (see plan §Order of
   changes 4-6).

## Session conventions

- Cowork sandbox: endplay installed via
  `pip install endplay --break-system-packages`; long runs must be
  time-budgeted (`CURATE_BUDGET`) — background processes don't survive
  between bash calls.
- Commits from Cowork: `git -c user.name="David Bailey"
  -c user.email="adavidbailey@gmail.com" commit ...`. **No push from
  Cowork** (no credentials, by David's choice) — David pushes from
  Terminal/Claude Code.
