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
- Open the intro chunk with `[show S]` to reveal the student's hand; reveal partner/opponents
  later as the narrative needs (often `[show NS]` near the end).
- Emit an anchored chunk for each **non-pass** call from the student's side. **Never anchor
  `[BID Pass]`.**
- Keep each chunk to ~2–4 short, conversational, second-person sentences. Ground the prose in
  the scenario's `btn/<scenario>.btn` `@chat` brief; if it teaches a decision tree, walk the
  student through it for *this* hand.
- Every `[BID xxx]` must match a real call in the auction. If you can't find a clean match,
  **drop the marker** rather than invent one — an unmatched `[BID]` degrades to the previous
  anchored chunk.
- Seat letters in `[show]` are **real compass** (the actual `[Deal]` seats); the trainer
  rotates everything so the student sits South on screen. Don't pre-rotate.

## Example (one board)

```
[Auction "S"]
1D    Pass  1H    Pass
2H    Pass  Pass  Pass
{[show S]
14 HCP, four good hearts headed by the \HAK, five diamonds, and the club \CAK. With no
five-card major, open your longer minor. Open one diamond.
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
