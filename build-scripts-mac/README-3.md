## Failed Scenarios (updated 2026-02-16)

Of the original 38 failures from the 2025-02-14 full build, **29 have been fixed**. **9 remain:**

All 9 remaining scenarios now complete the full pipeline (pbn, bba, filter, bidding sheet) but produce **0 boards after filtering** — the auction filter criteria are too restrictive for the newly-seeded hands.

**No boards after filtering (9):**

| Scenario | BBA Hands | Filtered Boards | Status |
|----------|-----------|-----------------|--------|
| Gerber_By_Responder | 500 | 0 | Released (2026-02-15) |
| Maximal_After_Overcall | 500 | 0 | Regenerated (2026-02-15) |
| Opps_Gambling_3N | 500 | 0 | Updated (2026-02-16) |
| Opps_Multi_2D | 500 | 0 | Updated (2026-02-16) |
| Responsive_Double | 500 | 0 | Updated (2026-02-16) |
| Snapdragon_Double | 500 | 0 | Updated (2026-02-16) |
| Spiral_Raises_with_3 | 500 | 0 | Updated (2026-02-16) |
| Weak_NT_10-12 | 500 | 0 | Updated (2026-02-16) |
| Preempt_Keycard | 500 | 0 | Updated (2026-02-16) |

### Previously failed, now fixed (2):

| Scenario | Filtered Boards | Status |
|----------|-----------------|--------|
| We_Overcall_NT_then_Smolen | 111 | Released (2026-02-16) |
| GIB_1M-P-Resp | 55 | Released (2026-02-16) |

### Root cause

These 9 scenarios generate 500 hands successfully and complete BBA analysis, but the auction filter matches 0 boards. The GIB robot's bidding doesn't produce the expected auction patterns with the new seed-generated hands. Options to resolve:
- Adjust auction filter patterns to be more permissive
- Increase `produce` count to get more candidate hands
- Regenerate with different seeds
- Review whether GIB's bidding conventions match the expected auctions
