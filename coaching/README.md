# `coaching/` — embedded tutorial PBNs for the Bridge Play Trainer

This directory holds the **coached** versions of scenario PBNs. Each file is a normal
PBN whose boards carry a Baker-Bridge–style `{...}` tutorial block, written so the
[Bridge Play Trainer](../Bridge%20Play%20Trainer.md) can teach the deal bid-by-bid and
during the play.

## How the trainer uses these files

- For a scenario, the trainer loads `coaching/<scenario>.pbn` if it exists, and falls
  back to `bba/<scenario>.pbn` (plain, no prose) otherwise.
- The trainer's **sidebar menu is restricted to scenarios that have a coaching file**, so
  in practice every user-pickable scenario is one that lives here.
- All prose is **precomputed** — the trainer makes no AI calls at runtime.

The authoritative parser is `parse_coaching` in the trainer repo's `server.py`
(`~/AI-Bridge-Play-Trainer`). When in doubt about behavior, that function is the source of
truth; this README documents its contract.

## ⚠️ Coaching depends on the convention card — regenerate after any card change

The coached **auctions are BBA's output under the scenario's `.bbsa` convention card**
(`convention-card-ns`/`-ew` in the `.btn`). If you edit a card, the `pbn/` / `bba/` /
`bba-filtered/` artifacts **and every coaching file built on them go stale** — they may
teach conventions the bots no longer bid (this bit us once: a "Basic Bridge" card had Bergen
and Jacoby 2NT turned off, but the coaching still described them). After any card edit:

1. Regenerate the pipeline from `pbn` onward: `python3 build-scripts-mac/pbs-pipeline-mac.py "<scenario>" "pbn+"`.
2. Rebuild the affected coaching files on the fresh auctions.

Deals are deterministic (fixed seed), so the **hands don't change — only the auctions and
contracts do**. To find stale files, diff each coached board's embedded auction against the
fresh `bba/` board for the same `[Deal]`.

## Play-of-the-hand scenarios (finesses, hold-ups, ruffs, endplays, top tricks)

These teach **declarer technique**, so the student is South/declarer and the bulk of each
block is the `[ROLE declarer][STAGE …]` play tips.

- **Curate the boards to the target contract.** Select ~30 boards where **South declares the
  intended contract** (filter the `bba-filtered/` source by `[Declarer "S"]` + the target
  `[Contract]`, e.g. Hold_Up_3N → `3N`, Side_Suit_Ruff → `4S`). The raw filter leaks slams,
  partscores, and boards where South isn't declarer — those don't show the lesson.
- **Analyze the actual deal**, not the idealized brief: where the key card sits, which
  defender is the danger hand, whether the finesse wins/loses on *this* layout. The prose
  must stay consistent with the board's `[Contract]`/`[Result]`/`[Score]`.
- **If a board doesn't fit the lesson, teach the real line and flag it** — never invent the
  textbook layout. (The dealer constraints often don't fully enforce the exact card
  placement, so a fraction of boards are off-pattern; tightening the `.btn` dealer code is
  the root fix.)
- Block layout mirrors `Play_Top_Tricks.pbn`: `[show S]` intro → `[BID]` per South call →
  `[POST-AUCTION]` (count winners/losers, name the technique, reveal partner via `[show NS]`
  as combined hands) → declarer/leader/defender `[ROLE][STAGE]` chunks, with praise only in
  `[STAGE post-play]`.

## File structure

Standard PBN. For each board you want coached, insert **one `{...}` block immediately
after the board's `[Auction "..."]` tag and its auction call lines** (before the next
`[Tag]`). Boards with no block just play normally. Only the curly block right after
`[Auction]` is read; any pre-auction `{Shape ...}`/`{HCP ...}`/`{Losers ...}` comments
from the `bba/` files are ignored.

The block body has up to three sections, **in this order**:

1. **Bidding tutorial** — an intro chunk plus one `[BID]`-anchored chunk per call.
2. **`[POST-AUCTION]`** — prose shown after the auction is fully revealed (contract summary
   etc.), before the Play hand-off.
3. **Card-play tips** — `[ROLE …][STAGE …]` chunks shown during play.

## Markers

| Marker | Meaning |
|---|---|
| `[show X]` | Reveal hand(s). `X` is one or more seat letters in **real compass** (`N E S W`) — e.g. `[show S]`, `[show NS]`. Reveals accumulate down the board. |
| `[BID xxx]` | Anchor the following prose to a call. `xxx` is PBN form: `1C 2D 3NT X XX`. Case-insensitive; `1N` and `1NT` are treated the same. Anchors to the next unconsumed matching call; when a call is ambiguous (e.g. several `Pass`es) the **student's own** call wins. Prose before the first `[BID]` is the intro chunk. |
| `[ACCEPT call …]` | Extra call(s) the bid-quiz should accept as correct alongside the one actually made — for judgment decisions with more than one defensible call (e.g. `[ACCEPT Pass]` after `1NT-2NT` with a middling hand). |
| `[POST-AUCTION]` | Begins the post-auction section (see above). |
| `[ROLE r][STAGE s]` | A card-play tip. `r` = `declarer` \| `leader` \| `defender`. `s` = `auction-end` \| `pre-lead` \| `post-lead` \| `post-play`. The trainer shows the chunk matching the student's role at that stage. |
| `\S \H \D \C` | Render as ♠ ♥ ♦ ♣. |

**Deferred reveals:** a `[show S]` (the student's own hand) is fine mid-auction, but any
`[show]` that exposes a hand the student can't yet see (partner/dummy, opponents) — and the
prose after it — is automatically held back and folded into the post-auction chunk, so a
hand is only described once it's visible. Author naturally; the parser handles the timing.

## Authoring rules

- Write from the **student's perspective**: "you" (S), "partner" (N), "LHO" (W), "RHO" (E).
  The student is normally South.
- **Voice: relaxed, warm, encouraging — like a friendly teacher at your shoulder, not a
  textbook.** The audience skews beginner/senior, so keep it conversational and supportive.
  Put **genuine praise in the reflective end-of-deal chunks** — the partner reveal,
  `[POST-AUCTION]`, and the `[ROLE …][STAGE post-play]` review — where a "nicely judged" or
  "that was the whole story — well played" lands naturally ("Twelve tricks, +650 — lovely
  result"). **Do NOT put praise ("Nice bid!") in a `[BID]` chunk:** those fire after *every*
  attempt, right or wrong, so praise there would also appear under a wrong answer. Per-bid,
  reactive praise is handled by the trainer app's own ✓/✗ quiz messages, not the prose. Stay
  warm and accurate — never sacrifice the bridge facts or the rules below for tone.
- Open the intro chunk with `[show S]` to reveal the student's hand; reveal partner/opponents
  later as the narrative needs (often `[show NS]` near the end).
- **The intro chunk poses the decision; it does not recite the hand or give the answer.** The
  student can see their own 13 cards, so don't list them (`You hold \S… \H… \D… \C…`), and
  don't name or hint the call. Frame it as: `You have <HCP> HCP and a <balanced |
  semi-balanced | unbalanced> hand[, with <a significant feature or two>]. What do you open?`
  (or `RHO opened 1X. What's your call?` in competitive scenarios). Vary the feature wording
  per hand — "a strong rebiddable six-card spade suit", "both majors", "5-5 in the minors",
  "no five-card major", "stoppers everywhere". Shape buckets: balanced = 4333/4432/5332;
  semi-balanced = 5422/6322; unbalanced = any singleton/void, 7+ suit, or two 5+ suits. The
  `[BID xxx]` chunks come *after* the call, so they freely explain the bid — that's where the
  teaching goes, not the intro.
- **1♦ opening rule (Basic-Bridge):** a 1♦ opener normally has 4+ diamonds. The only exception
  is when the distribution is exactly 4=4=3=2. With 3-2 in the minors, open the 3-card suit.
- Emit an anchored chunk for each **non-pass** call from the student's side. **Never anchor
  `[BID Pass]`.**
- **When you reveal partner with `[show NS]`, describe the *combined* hands — the fit, the
  combined strength, and the weakness — not partner's 13 cards.** Once revealed, partner's
  hand is on screen, so a card-by-card list (`Partner: \S… \H… \D… \C…`) is redundant.
  Name the trump/notrump fit and its combined length, where the partnership's power lives
  (controls, a running suit, ruffing values), and the soft spot (a leaky short suit, a
  missing stopper, thin trumps, a 4-3 fit, a misfit), then keep the contract/result takeaway.
  Reference a specific honor only when it makes a teaching point (a fitting honor, a control
  opposite shortness) — never to enumerate the hand.
- Keep each chunk to ~2–4 short, conversational, second-person sentences. Ground the prose in
  the scenario's `btn/<scenario>.btn` `@chat` brief; if it teaches a decision tree, walk the
  student through it for *this* hand.
- Every `[BID xxx]` must match a real call in the auction. If you can't find a clean match,
  **drop the marker** rather than invent one — an unmatched `[BID]` degrades to the previous
  anchored chunk.
- Seat letters in `[show]` are **real compass** (the actual `[Deal]` seats); the trainer
  rotates everything so the student sits South on screen. Don't pre-rotate.

## Bridge accuracy in the prose

Beyond the structural rules above, keep the bridge correct and the wording precise:

- **Balanced vs. unbalanced.** Balanced = 4-3-3-3, 4-4-3-2, 5-3-3-2 (no singleton or void, at
  most one doubleton). Semi-balanced = 5-4-2-2 or 6-3-2-2. **Any singleton or void makes a hand
  unbalanced, regardless of HCP** — never call a singleton-bearing hand "balanced" or
  "balanced-ish" (e.g. 1-4-5-3 is unbalanced).
- **Diagnose the real reason a bid is rejected.** If a hand is in the point range for a call but
  can't make it, the reason is usually *shape*, not strength. 15 HCP is plenty for 1NT (15-17) —
  if you're not bidding 1NT, say the hand is **unbalanced / unsuitable**, not "not strong enough."
- **Opening-suit algorithm (Basic-Bridge).** A biddable major is 5+, a biddable minor is 3+.
  Open the longer biddable suit; with equal length open the **higher-ranking**; with exactly
  **3-3 in the minors open 1♣ (the short club)**. A 1♦ opener normally has 4+ diamonds — the only
  exception is exactly 4=4=3=2 (open the 3-card diamond). With two 5-card suits, open the
  **higher-ranking** (5-5 spades-and-diamonds → 1♠).
- **Reverse, defined correctly.** A reverse is a new-suit rebid **higher-ranking than your first
  suit** that forces partner to the three-level to show preference; it promises extras (~17+) and
  is forcing for one round. A second suit **lower-ranking** than your first — so partner can give
  preference at the two-level — is **not** a reverse; it's a natural, wide-range rebid (~11-16
  HCP). For example **1♦-1♠-2♣ is natural** (4+♦, 4+♣, fewer than three spades), not a reverse.
- **Geometry words.** Partner sits **opposite** you, across the table — describe partner's holding
  as "♦KJT73 opposite your ♦AQ862," never "behind." "Behind" / "in front of" describe an
  *opponent's* positional relationship during the play, not partner.
- **Terminology.** Choose the **higher-ranking** suit (not just "the higher"); a misfit is a
  **lack of a fit** (not "no second suit between you").
- **No thinking-out-loud.** Finished prose states the conclusion. Don't leave "Wait —,"
  "actually," or visible self-corrections in the text.

## Example (one board)

```
[Auction "S"]
1D    Pass  1H    Pass
2H    Pass  Pass  Pass
{[show S]
You have 14 HCP and a semi-balanced hand with five diamonds, four good hearts, and no
five-card major. What do you open?
[BID 1D] You have 14 HCP and five diamonds. With no five-card major, open one diamond.
[BID 2H] Partner showed four+ hearts. You hold four to the ace-king — raise to two hearts
and let partner declare.
[POST-AUCTION]
Your side has 23 combined HCP and an eight-card heart fit. Two hearts needs eight tricks.
[ROLE declarer][STAGE auction-end]
Partner declares; your hand is dummy. With the \HAK and \CAK this dummy carries real power.
[ROLE leader][STAGE pre-lead]
Lead the \DA, top of your \DAK. Cash a winner first and look at dummy before continuing.
[ROLE declarer][STAGE post-play]
Drawing trumps and cashing your AKs was all you needed — no finesse to reach eight tricks.
}
```

## See also

- **Generation/authoring plan** (how these files get produced, including the subagent
  prompt template): `pbn-coaching-generator-plan.md` in the trainer repo
  (`~/AI-Bridge-Play-Trainer`).
- **Parser contract:** `parse_coaching` / `_strip_post_auction_blocks` in that repo's
  `server.py`.

> Note: `[hint]` / `[wrong xxx]` per-bid miss-prose are **proposed but not yet implemented**
> (see the generator plan's "Followups"). Don't author them yet — the parser ignores them.
</content>
