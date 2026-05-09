# BBA Bidding Evaluation — Fourth Suit Forcing scenario

**Date:** 2026-05-07
**Tester:** David Bailey (with Claude as kibitzer)
**Tool:** Bridge Classroom solo-practice (`bridge-classroom.com/solo-practice-app/#/bidding-practice`)
**Scenario:** Fourth Suit Forcing (PBS)
**Convention cards:** NS=21GF-SPECIALS, EW=21GF-GIB
**Conditions:** All vul, Dealer N
**Sample size:** 3 hands (Deals 3, 176, 181 of 193)

---

## Hand 1 — Deal 3 of 193 ✅ BBA correct

**South:** ♠J3 ♥A9764 ♦AKQ8 ♣97 (14 HCP)
**Auction:** 1♣–P–1♥–P–1♠–P–2♦(NMF)–P–3♣–P–**?**

| Bidder | Pick | Result |
|---|---|---|
| BBA | 3♥ | finds 5-3 heart fit; 4♥= makes 10 (+620) |
| Human | 3NT | made 9 (+600) |

**Verdict:** BBA's 3♥ rebid after NMF is the right tool — keeps the 5-3 major-fit search alive when opener's 3♣ doesn't deny 3-card support. Good behavior.

---

## Hand 2 — Deal 176 of 193 ⚠️ BBA misses slam in 4-4 minor

**South:** ♠A9 ♥AJ742 ♦KQ109 ♣102 (14 HCP)
**Auction (BBA recommendation followed):** 1♦–P–1♥–P–1♠–P–2♣(NMF)–P–3♣–P–3NT–P–P–P
**Final contract:** 3NT by N, **made 10**

**Double-dummy:**

| Strain | ♣ | ♦ | ♥ | ♠ | NT |
|---|---|---|---|---|---|
| N/S tricks | 10 | **12** | 9 | 10 | 10 |

**6♦ makes 12** — slam missed. ~730 IMPs lost vs. par.

**Verdict:** Responder holds two aces (♠A ♥A), ♦KQ109 (4-card support for opener's diamonds), and ♣102 (partner short in clubs implied by their 1♠ rebid). The 4-4 minor fit produces 2 extra ruffing tricks NT can't access. BBA's algorithm doesn't trigger slam exploration here, even with classic slam-positive controls and a known fit.

**Suggested investigation:** Does BBA recognize 4-4 minor fits as slam-worthy when responder has aces + KQ-of-trumps + length? Currently the algorithm appears to settle for 3NT once a stopper-rich game is reached.

---

## Hand 3 — Deal 181 of 193 ⚠️ BBA misses slam invite via cuebidding

**South:** ♠KQ3 ♥AK1053 ♦QJ107 ♣2 (15 HCP)
**Auction (human path):** 1♣–P–1♥–P–1♠–P–2♦(NMF)–P–3♣–P–**3♠**–P–4♣–P–**4♥**–P–4NT–P–5♠–P–**6♠** — made 12 ✅

**BBA divergences:**

| Round | Human | BBA |
|---|---|---|
| 4 (after 3♣) | 3♠ (show fit) | 3♥ (show 5 hearts) |
| 5 (after 4♣) | 4♥ (cuebid) | 4♠ (sign-off) |

**Following BBA's path:** lands in 4♠ game — missing slam.
**Following cuebid path:** lands in 6♠, made 12 (+1430 vs +650).

**Verdict:** BBA's algorithm undervalues cuebids when responder has 3-card support + singleton + ace-rich. After partner cuebid 4♣ (which BBA's opener algorithm itself produced), BBA wanted responder to retreat to 4♠ rather than reciprocate with 4♥.

**Suggested investigation:** When opener cuebids in a 3♣-jump-rebid auction, does responder's algorithm continue the cuebid sequence on slam-positive hands, or fall back to fast-arrival sign-off?

---

## Patterns observed

1. **Hand 1** — BBA's 3♥-after-NMF is correctly tuned ✓
2. **Hands 2 & 3** — BBA misses slam in two distinct ways:
   - **Hand 2:** No slam exploration despite 4-4 minor fit + strong responder controls
   - **Hand 3:** Doesn't follow up on its own cuebid; treats responder's 3-card support as game-only

Both slam misses stem from auctions starting with responder's NMF. BBA's NMF-followup logic appears conservative when responder has high cards and shape for slam, even after opener has shown extras (3♣ jump rebid).

---

## Sample size caveat

Three hands is a small sample. The patterns above are suggestive, not conclusive. Recommend running 20-30 more hands from this scenario before drawing firm conclusions about BBA's NMF/slam logic.
