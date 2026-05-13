# Bidding Session — 2026-05-12

Today was mostly **convention learning + tooling work** rather than score-tracking. The Serious deals were practice-only (you instructed "disregard BBA comparison" since BBA doesn't play Serious).

## Bidding practice

| Run | Scenarios | Deals | Notes |
|---|---|---|---|
| 1 | Serious | 5 | First introduction; before knowing the rules properly |
| 2 | Serious | 5 | After your initial rules explanation |
| 3 | Serious | 10 | Applied Serious cuebid logic — some slams found, one grand missed (deal 7♥), one disaster (7♥−1 missing ♠K) |
| 4 | Serious | 5 | After full convention rules + "skip denies" + "cue after denial = two controls" clarifications |

Three slams reached and made on the practice deals (6♣, 6♥, 6♠); one grand made (7♥); a couple slams overbid down. The Serious sequence demonstrated clearly when both partners follow it.

## Serious Cue Bids — convention learned

Full rules captured in [reference_serious_cue_bids.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_serious_cue_bids.md):

- **Trigger**: major fit found and last bid is 3M
- **3NT** = "not serious, cooperative"
- **4M** = "minimum, hope we make it"
- **Other bid** = serious cue showing 1st or 2nd round control
- **Cues go up the line, including 3-of-other-major** (e.g., 3♠ after 3♥ trump fit)
- **A skip denies a control** in the skipped suit
- **A cue after partner's denial requires control in the denied suit** AND shows control in the new suit — so it's effectively a *two-control bid*
- **Robots don't play Serious** — bid natural cues against BBA; play Serious only with human partners (the Bridge Classroom Bidding Table will eventually support human partners)

Key insight: with Serious, **you never invoke RKCB with an uncontrolled side suit** — every cuebid either confirms or refines side-suit controls before the keycard ask.

## Serious vs Standard Cue Bidding — statistical analysis

Wrote a full analysis: [serious-cuebids-analysis-2026-05-12.md](serious-cuebids-analysis-2026-05-12.md).

Headline findings (Pass 2, less-biased dataset of 158,600 deals):
- **9,116 RKCB-after-major-fit auctions** analyzed
- **157 Serious-avoidable disasters** (1.7% rate)
- 100% of "missing both 1st & 2nd round side-suit control" slams went down — Serious would have prevented every one
- ~0.24 IMPs/deal expected gain from Serious in RKCB-major-fit auctions
- The Pass 1 (biased toward slam-zone hands via `keep03`/`keep44` leveling) showed the same per-RKCB rate

Comparison section also covered **Non-Serious 3NT vs Serious 3NT** (mirror-image variants). Recommendation: Non-Serious 3NT (Rodwell-style) for partner-portability and matching the cheap-bid-weak-meaning principle.

## New Puppet Stayman scenarios

Built and pushed two new scenarios:

| File | Opener | bbsa | Filter |
|---|---|---|---|
| Puppet_Stayman_1N.btn | 1NT (15-17) | **21GF-Puppet** (new — diff from 21GF-DEFAULT: `1N-3C Puppet = 1`, `1N-3C transfer to diamonds = 0`) | `Note....1N-3C Puppet` |
| Puppet_Stayman_2N.btn | 2NT (20-21) | 21GF-MSTandMSS | `Note....2N-3C Puppet` |

Both added to `-button-layout-beta.txt` (1N in Notrump Sequences section, 2N near other 2N scenarios). Replaced the older `2N_Puppet` entry. Smolen_after_2N moved to its own row.

Convention documentation in each .btn references [bridgebum.com/puppet_stayman.php](https://www.bridgebum.com/puppet_stayman.php).

## New memory files created today

- [reference_serious_cue_bids.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_serious_cue_bids.md) — full Serious convention, including the "cue after denial = two controls" rule and the "RKCB always safe" property
- [feedback_1d_open_with_short_diamonds.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/feedback_1d_open_with_short_diamonds.md) — 1♦ open with <4♦ only with exactly 4-4-3-2 shape (4♠ 4♥ 3♦ 2♣)

## Workflow notes

- `bba/Serious.pbn` has `keep03` for game-zone (97% throw-away rate) → analysis was biased toward keycard-rich hands until Pass 2 broadened the sample to all `bba/` files
- BBA's `[Note "X:2N-3C Puppet Stayman"]` annotation provides the auction-filter mechanism for Puppet Stayman scenarios
- Pipeline runs are fast (~6s each for new scenarios); generates dlr → pbs → pbn → rotate → bba → filter → bidding-sheets → quiz → package files

## Open items

- Run `Puppet_Stayman_1N`/`Puppet_Stayman_2N` in actual bidding sessions to validate the scenarios work as intended
- Consider analogous "non-serious 3NT" scenario variant (or document that the Serious scenario already covers both, since the difference is in cue-meaning only)
