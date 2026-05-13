# Bidding Session — 2026-05-11

## Scenarios bid

- **Inverted Minors** (21GF-DEFAULT) — early session
- **Fit Showing Jumps** (21GF-GIB) — interleaved with Inverted Minors
- **New Minor Forcing** (21GF-DEFAULT) — later session
- **Fourth Suit Forcing** (21GF-SPECIALS) — later session

## Score by run

| Run | Scenarios | Deals | BBA / Me (BAM) | Net IMPs |
|---|---|---|---|---|
| 1 | Inverted Minors | 5 | 3.0 / 2.0 | −15 |
| 2 | Inv Minors + FSJ | 10 | 5.5 / 4.5 | −6 |
| 3 | Inv Minors + FSJ | 10 | 5.0 / 5.0 | 0 |
| 4 | NMF + FSF | 10 | 5.5 / 4.5 | −7 |
| 5 | NMF + FSF | 10 | 5.5 / 4.5 | −18 |
| 6 | NMF + FSF, Random Rotate | 10 | 6.0 / 4.0 | ~−3 |
| **Total** | | **55** | **30.5 / 24.5** | **~−49** |

## New memories created

- [reference_gib_inverted_minor_opener_3nt.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_gib_inverted_minor_opener_3nt.md) — GIB's definition of 1m-2m-3NT
- [reference_gib_vs_bba.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_gib_vs_bba.md) — Differences between the two robots
- [reference_bridge_classroom_bidding_table.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_bridge_classroom_bidding_table.md) — Random scenario+deal selection
- [reference_bridge_classroom_url.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_bridge_classroom_url.md) — bridge-classroom.com bookmark
- [reference_nmf_unbid_minor.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_nmf_unbid_minor.md) — NMF is the unbid minor (2♣ after 1♦, 2♦ after 1♣)
- [feedback_fsf_as_natural.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/feedback_fsf_as_natural.md) — Prefer FSF with real length in the 4th suit
- [feedback_4nt_after_3nt_signoff.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/feedback_4nt_after_3nt_signoff.md) — After 3NT signoff, 4NT may be NATURAL in BBA; use cuebids
- [feedback_kill_stale_chrome_9222.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/feedback_kill_stale_chrome_9222.md) — Kill stale Chrome on port 9222 without asking
- Updated [reference_bba.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/reference_bba.md) — BBA has no per-auction definition site
- Updated [feedback_bbsa_first_then_bid.md](.claude/projects/-Users-adavidbailey-Practice-Bidding-Scenarios/memory/feedback_bbsa_first_then_bid.md) — Re-check CC when scenario changes mid-session

## Recurring lessons (biggest losses)

1. **Deal 151 (FSF) — −12 IMPs.** With 7-card hearts + 15 HCP after partner's 1♣, jumped to 2♥ (2/1 GF) instead of bidding 1♥. The slow auction would have let partner show 4-card spades; instead the auction spiraled into a 7♠−3 disaster.
2. **Deal 285 (Inverted Minors) — −12 IMPs.** With 4-4-4-1 + 16 HCP + 3 aces + ♦ fit, passed partner's 3NT instead of pushing slam (4♦ try). 6♦ was cold.
3. **Deal 5 of NMF/FSF run — −14 IMPs.** With 4-card ♣ support + 14 HCP + singleton + 3 aces, took the 3♣ direct raise instead of routing through 4SF. Partner had slam values and passed.
4. **Deal 10 of NMF/FSF run — −14 IMPs.** After partner's reverse + 3NT signoff, 4NT was treated as NATURAL (partner passed). BBA's 4♦ cuebid would have driven to 7♦ grand.

## Tools & workflow

- **bid.js** (port 9222) connects to bid.js Chrome
- **Playwright MCP** uses a separate browser session (about:blank) — can't reach the BBA practice session
- **Stale Chrome zombie on port 9222** — kill PID and re-run start-chrome.sh
- **Bridge Classroom Bidding Table URL:** https://bridge-classroom.com/solo-practice-app/#/bidding-practice
- **Random Rotate checkbox** flips dealer 180° — gives a mix of opener and responder hands; the user enabled this for run #6

## Open questions / next steps

- Verify NMF behavior with both unbid minors (1♥-1♠-1NT): one data point said BBA prefers 2♦, another said 2♣. Inconclusive.
- BBA seems to consistently miss slams that I or it could find with stronger slam-bidding tools. Several +630 results when slam was on.
- Practice OPENER-side bidding more — Random Rotate gave me ~70% opener deals in run #6 and exposed gaps (deal 161: when to reject partner's invite).
