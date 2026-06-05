# Bookmark — bba-curated scoping (2026-06-03)

> **SUPERSEDED 2026-06-04 by [pbn-curation-plan.md](pbn-curation-plan.md).**
> Two decisions changed after this note: (1) curate reads the full **`bba/`**
> pool, not `bba-filtered/` — the `.btn` regex is demoted to a per-board
> feature (`matched_intended_auction`), no longer a gate; (2) selection is
> tier-based (Layer B grading), not a single best-N sort. Layer A has since
> run over all 19 scenarios — see `bba-curated/-overnight-summary.md`.

Discussion stopped here: scoping the `curate` step that reads `bba-filtered/` and creates `bba-curated/`.

## Where things stand

- `bba-filtered/`: 320 scenario `.pbn`/`.pdf` pairs — on-pattern but unscored pool.
- `coaching/`: 20 hand-authored 30-board lesson sets (the curation target per the proposal).
- `bba-curated/` does not exist yet — it would be the scored, best-N selection between `filter` and authoring.
- Prototype exists: `curation_trial.py` (PBN parser + DD gate via `endplay`; validated in `Coaching-Board-Curation-Proposal.md`).

## Agreed scope (Phase 1 only)

1. Generalize the parser to walk all of `bba-filtered/`.
2. DD quality gate: soundness from South, wrong-sided detection, by-force honor-swap test.
3. Selection: pick best N (30?), deterministic sort key, decide rotate-salvage vs discard for wrong-sided.
4. Emit `bba-curated/<scenario>.pbn` + regenerate matching `.pdf`.

Phase 2 (single-dummy Monte-Carlo for avoidance lessons) is explicitly out of scope — designed, not built.

## Open question (unresolved — answer this on resume)

Should `bba-curated/` cover **all 320** filtered scenarios, or **only the ~20 coaching play lessons**? This drives selection logic (by-force/avoidance gating applies only to play lessons) and runtime.

## Next action offered

Draft the `curate` script — generalize `curation_trial.py` to read all of `bba-filtered/` and write `bba-curated/`.

Note: `endplay` is installed on the Mac but not in the Cowork sandbox; curation runs locally.
