# Bridge Play Trainer — Sample Transcript

**Date:** 2026-05-14
**Purpose:** Hand-rolled walkthrough of one full deal to validate the per-trick experience before any code is written.

User plays declarer (South). Mode: **Play**. Signaling: standard attitude / standard count. Opening lead policy: realistic human heuristic.

---

## Scenario: Major Suit Fit · Deal #1 (constructed)

### Auction

| W | N | E | S |
|---|---|---|---|
| | | | 1♠ |
| Pass | 3♠ | Pass | 4♠ |
| Pass | Pass | Pass | |

**Contract: 4♠ by South. Vul: None.**

### Hands (you see your own + dummy)

```
                North (dummy)
            ♠ K 9 8 2
            ♥ 9 7
            ♦ A J 8 5
            ♣ Q 7 4

West ──┐                       ┌── East
       (hidden)                (hidden)

                South (you)
            ♠ A Q J 5 4
            ♥ A 8
            ♦ K 7 2
            ♣ J 6 3
```

---

## Trick 1

**West leads ♥K.**

```
                North
            ♣ Q 7 4   ♦ A J 8 5   ♥ 9 7   ♠ K 9 8 2
                  Trick 1 to West
                       ♥ ?
West: ♥K ─────────────────────── East: ?

                South
            ♣ J 6 3   ♦ K 7 2   ♥ A 8   ♠ A Q J 5 4
```

> **Trainer:** Plan your play. What's your current read on West and East?

> **You (user):** West has ♥KQJ for sure — top of sequence. Probably 4+ hearts. They passed throughout — between 6 and 11 HCP roughly. East is also a passed hand throughout.

> **Trainer feedback:**
> - ✅ **♥KQJ correctly inferred** — top-of-sequence lead reliably shows two touching honors below.
> - ✅ **West's HCP ceiling**: passing throughout with the auction at the 3-level rules out a 2-level overcall. Standard 2-level overcall needs ~10+ HCP and a decent suit. West has a perfectly fine 5+ heart suit if they have one, so passing means **either fewer than 5 hearts OR weaker than 10 HCP**. Your "6–11 HCP" is generous; tighten it to **8–11 HCP** since W has ♥KQJ which is already 6 HCP.
> - ⚠️ **Heart length**: with KQJ + 4 hearts, West would happily overcall 2♥. So **West probably has only 4 hearts** (KQJx). If 5+ hearts they likely would have overcalled. This is a strong inference you missed.
> - 🎯 **Watch trick 1's signal**: East's card on this trick will be attitude (high = "play hearts back", low = "no help here"). Note what East plays.
>
> **Try the play first.** Win ♥A in hand or duck? With ♥AK out and West likely with QJ, you have one heart loser regardless. Ducking gains tempo if East has ♣A (unlikely to find it), but standard play is win ♥A and start drawing trumps.

> **You play:** ♥A (winning trick 1).
>
> West plays ♥K. North (dummy) plays ♥7. East plays ♥**2**. You win in hand with ♥A.

> **Trainer note:** East played ♥2 — **low card, discouraging attitude**. East doesn't want hearts continued. This is mild evidence East has a heart honor (so doesn't want to set it up) OR weak hearts (so wants partner to switch). Combined with the auction silence, the latter is more likely.

---

## Trick 2

You lead ♠5 from hand toward dummy's ♠K982. Plan: try to drop ♠10 by playing for honors split.

```
                North
            ♣ Q 7 4   ♦ A J 8 5   ♥ 9    ♠ K 9 8 2
                  Trick 2 led by South
                       ♠ ?
West: ?  ─────────────────────── East: ?

                South
            ♣ J 6 3   ♦ K 7 2   ♥ 8    ♠ A Q J 4
```

> **Trainer:** Before you play to this trick, what new info do you have, and what's your updated read?

> **You:** East's low ♥ signal was discouraging — they probably have no ♥ honor. West has 8–11 HCP with ♥KQJ (6 of it), so West has another 2–5 HCP somewhere. East has at most 14 HCP total minus West's 11, so ~12 HCP between them with 6 in W's hearts, leaving ~6 HCP across all other cards. Distribution still unclear.

> **Trainer feedback:**
> - ✅ **East has no heart honor** — discouraging signal + the fact that W has KQJ leaves only ♥10x for East at most. Solid inference.
> - ✅ **HCP breakdown**: NS has 25 (your 15 + dummy's 10). EW must have 15 total. W has 8–11 (likely 8–10), so **E has 4–7 HCP**.
> - ⚠️ **Refinement on W's length**: you didn't update W's heart length given E's discouraging signal. If E has ♥10xx or ♥10x, then W has KQJ + ? hearts. W passed → only 4 hearts (would have overcalled with 5). So W is exactly **♥KQJ + one small** = ♥KQJx, 4 cards. E has the remaining 7 hearts? No wait, 13 hearts total - your 2 - dummy's 2 - W's 4 = **E has 5 hearts**. Update your estimate!
> - 🎯 **Now plan the spade play**: you have ♠AQJ54 opposite ♠K982. Missing ♠10763 (4 cards in E/W). The key is whether ♠10 drops in 3 rounds or if you can finesse against it. **Standard play: play ♠A first, then small to ♠K, hoping for 3-2 break with ♠10 doubleton.**

> **You play:** ♠5 to dummy's ♠K.

> **W: ♠6, N: ♠K (wins), E: ♠3.**

---

## Trick 3

```
                North
            ♣ Q 7 4   ♦ A J 8 5   ♥ 9    ♠ 9 8 2
                  Trick 3 led by North
                       ♠ ?
West: ?  ─────────────────────── East: ?

                South
            ♣ J 6 3   ♦ K 7 2   ♥ 8    ♠ A Q J 4
```

> **Trainer:** Both defenders followed small in spades. What do you read?

> **You:** Both followed with small spades (♠6 and ♠3). No info about ♠10 yet. Could split 3-1 either way.

> **Trainer feedback:**
> - ⚠️ **Missed inference**: when defenders play ♠6 and ♠3, you saw the **♠3** from East. Together with E's earlier ♥2, E is signaling consistently low — likely showing **odd count** in spades under standard count. East with ♠3 first time suggests an odd number of spades (1 or 3).
> - 💡 **Better inference**: count signals are often unreliable here because both ♠3 and ♠6 are "small," but the ♠3 specifically is the lowest possible spot card. East with a singleton ♠ would play it; East with three small (♠3-6-something) would play low-high. So far ambiguous.
> - 🎯 **Next play**: continue with ♠2 from dummy to your ♠J or ♠Q, finessing through East. Wait — there's no ♠10 finesse needed since you have the rest of the honors. Play ♠Q (or ♠J) from hand to test for the ♠10.

> **You play:** ♠2 from dummy, ♠Q from hand.

> **N: ♠2, E: ♠10 (drops!), S: ♠Q (wins), W: ♠7.**
>
> **Trump count: 4 trumps in defenders' hands. Now drawn 3 rounds. ♠10 has fallen.** Distribution clear: W started with ♠76, E with ♠103. Both have **2 spades**.

---

## Trick 4

```
                North
            ♣ Q 7 4   ♦ A J 8 5   ♥ 9    ♠ 9 8
                  Trick 4 led by South
                       ♠ ?

                South
            ♣ J 6 3   ♦ K 7 2   ♥ 8    ♠ A J 4
```

> **Trainer:** You're at a great juncture. Update your read on E/W.
>
> Use **structured form** from this trick on:

| | Spades | Hearts | Diamonds | Clubs | HCP |
|---|---|---|---|---|---|
| West | __ | __ | __ | __ | __ |
| East | __ | __ | __ | __ | __ |

> **You enter:**

| | ♠ | ♥ | ♦ | ♣ | HCP |
|---|---|---|---|---|---|
| West | 2 | 4 | 4 | 3 | 9 |
| East | 2 | 5 | 3 | 3 | 6 |

> **Trainer feedback:**
> - ✅ **Spades correct**: 2 each, confirmed.
> - ✅ **West's hearts (4)**: correct given the auction inference + KQJ.
> - ✅ **East's hearts (5)**: math checks: 13 − 4 (W) − 2 (dummy) − 2 (you) = 5 in East. Correct.
> - ⚠️ **Diamonds and clubs uncertain**: nothing has been played in either. Your 4-3 / 3-3 split is a guess.
> - ⚠️ **HCP**: W has ♥KQJ (6), so 9 HCP estimate means W has 3 more HCP somewhere. Maybe ♦Q? ♣K? Unknown. **Plausible.**
> - 🎯 **Next plan**: you have one more trump to draw (West has the last one). Then you need to think about ♣ losers — ♣A might be with East, who's been silent. Play your way through the rest carefully.

> **You play:** ♠4 to dummy's ♠9, then ♠8 — pulls W's last trump. Trump count: 0 outstanding.

(Tricks 4-5 collapsed: draws last trump from West.)

---

## Trick 6

After drawing trumps, you've played ♠AKQJ + the ♠5/♠4 — five spade tricks. Now in dummy, you lead ♦A.

```
                North
            ♣ Q 7 4   ♦ A J 8 5   ♥ 9    ♠ —

                South
            ♣ J 6 3   ♦ K 7 2   ♥ 8    ♠ —
```

> You lead ♦A from dummy.
>
> **W: ♦3, N: ♦A (wins), E: ♦4.**

> **Trainer:** What does the diamond play tell you?

> **You:** Both defenders followed with small. East's ♦4 is low — discouraging or low-from-something.

> **Trainer feedback:**
> - ✅ **Both following small** confirms diamonds are at least 3-3 (no singleton). Now you know each defender has at least 1 more diamond.
> - 🎯 **Update length**: Diamonds 13 total - your 3 - dummy's 4 = 6 EW. We've seen 2. Each defender has 2 more or split 3-3.

> **You play:** ♦5 from dummy → ♦2 from your hand. W: ♦Q (wins), N: ♦5, S: ♦2, E: ♦9.
>
> **W's ♦Q wins the trick.** Update: W has ♦Q (so far had ♦3, ♦Q). E showed ♦4, ♦9.

---

## Trick 7

> **Trainer:** West just won ♦Q. Update your read.

> **You update:**

| | ♠ | ♥ | ♦ | ♣ | HCP |
|---|---|---|---|---|---|
| West | 2 | 4 | 4 | 3 | 10 |
| East | 2 | 5 | 3 | 3 | 5 |

> **Trainer feedback:**
> - ✅ **W's ♦Q nailed**. Bumped HCP estimate appropriately (W now 10, from 9).
> - ⚠️ **♦ distribution still tentative**: W showed ♦Q3 so far (2 cards), E showed ♦94 (2 cards). 4 ♦ remain in EW (out of original 6). If 4-2 split, W could have ♦ Q-3-x-x and E ♦94. If 3-3, W has ♦Q-3-x and E ♦9-4-x.
> - 💡 **Hint**: East's ♦9 looks like it might be a "high-low" count signal start, suggesting **even count** in diamonds (so East has 4 diamonds). If true, W has just **2 diamonds** (Q3) and E has 4 (9-4-x-x).
> - 🎯 If East has 4 diamonds, W started 2-4-2-5 (♠2-♥4-♦2-♣5)? Let's see — does W have 5 clubs? With ♥KQJ + ♦Q3 + ♠76 + ♣? = 13. 13-2-4-2 = 5 ♣ ✓. So W is **2-4-2-5**.

> **West leads ♦Q ... wait, W already played ♦Q and won.** West now leads to trick 7.
>
> **W leads ♣2.** Dummy follows ♣4, E plays ♣A (winning), S plays ♣3.
>
> **East takes ♣A.**

---

## Trick 8 onward (collapsed)

Quick walkthrough:
- E returns ♣9. S plays ♣J (loses to W's ♣K). W cashes ♥Q.
- **Final count**: declarer 10 tricks. 4♠ making exactly = +420.

End-of-deal summary:

| | ♠ | ♥ | ♦ | ♣ | HCP |
|---|---|---|---|---|---|
| **Actual West** | 2 | 4 | 2 | 5 | 10 |
| **Your last estimate** | 2 | 4 | 4 | 3 | 10 |
| **Actual East** | 2 | 5 | 4 | 2 | 5 |
| **Your last estimate** | 2 | 5 | 3 | 3 | 5 |

---

## End-of-deal scoring (trainer)

| Inference | Result |
|---|---|
| Trick 1 — ♥KQJ in W | ✅ Full credit |
| Trick 1 — W's heart length | ⚠️ Missed "exactly 4" inference |
| Trick 2 — E has no heart honor | ✅ Full credit |
| Trick 3 — ♠10 drop | ✅ Followed correctly |
| Trick 4 — ♠ count (2 each) | ✅ Full credit |
| Trick 6 — W's ♦Q | ✅ Full credit |
| Trick 7 — ♦ split | ❌ Got the split wrong (predicted 4-3, actual 2-4) |
| Trick 7 — ♣ length implication | ❌ Missed: if W has 2 ♦ + 4 ♥ + 2 ♠, must have 5 ♣ |

**Final: 5/8 = 63% inferences correct.**

**Lesson from this deal**: when one defender's length is known in three suits, the fourth is determined. W's confirmed 2-4 in ♠/♥ + your observation of his ♦Q-low play could have pinned down a 2-2 in ♦/♣ split. Watch for the moment **three suits are constrained** — the fourth is then forced.

---

## What this transcript tells us

**The interaction model works:**
- Per-trick prompt + free-text input is natural and educational.
- Switching to structured form at trick 4 forces precision exactly when defenders' cards start providing real evidence.
- Trainer feedback combines: (1) confirmation of correct inferences, (2) what you missed, (3) hint for next trick.
- End-of-deal scoring on the inferences themselves (not card-play) makes the *thinking* visible.

**Things this surfaces that the design spec didn't fully capture:**
- The trainer should **track which inferences the user got right/wrong** across the whole deal and surface them at end.
- The "missed inference" feedback is most valuable when it's about something **the user could have known but didn't articulate** — vs unknowable info.
- Free-text mode is comfortable through trick 3–4; **structured mode kicks in around trick 4** when enough info has accumulated.
- **One-line "watch for next trick" hint** at the end of each evaluation gives the user something to look for. Very high-value addition.

**Next:** does this experience feel right? If yes, we proceed to a minimal web UI + Python backend.
