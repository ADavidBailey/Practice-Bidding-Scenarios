# Play-coaching generator — authoring spec

How the **card-play** coaching for the 12 play scenarios (Finesses, Notrump
Play, Suit Contract Play) is written into `coaching-curated/<scenario>.pbn`.
This is the play counterpart of `GENERATOR.md` (bidding). It uses the trainer's
EXISTING `[ROLE]/[STAGE]` tip machinery — no trainer changes needed.

The student declares (South) and the lesson teaches one play technique (the
board's curated `declarer` theme: hold-up, finesse-safe-hand, establish-long-
suit, ruff-in-dummy, …). Selection comes from the curation: pick boards graded
`declarer: textbook`/`standard` for the target theme (and, for hold-up,
`holdup_required: true` from Layer A).

## What goes in the `{ ... }` block

Per board, after the `[Auction]`, the block holds an optional brief bidding
part (these auctions are short/fixed — keep it minimal or omit) followed by
the PLAY TIPS, which are `[ROLE r][STAGE s]`-anchored chunks. The trainer
fires each tip at its stage. Stages: `auction-end`, `pre-lead`, `post-lead`,
`post-play`. Roles: `declarer`, `leader`, `defender`.

Emit these tips (declarer-focused; the UI centers on declarer):

1. `[ROLE leader][STAGE pre-lead]` — **REQUIRED and load-bearing.** It MUST
   start with `Lead the \Xr` naming a SPECIFIC card, suit escape directly
   before the rank, NO space (`\HK`, never `\H K` — a space stops the parser
   extracting the card for the auto-lead). The card is the correct standard
   opening lead from the OPENING LEADER's hand (declarer's LHO = West when
   South declares):
   - vs notrump: 4th-best from the longest, strongest suit (or top of a 3+
     touching-honor sequence).
   - vs a suit contract: a SMALL singleton (a spot card — NEVER a singleton
     honor A/K/Q/J), else partner's bid suit, else top of a touching-honor
     sequence, else 4th-best from the longest suit.
   - card from a holding: top of a sequence/interior sequence; 4th-best from
     length; low from three small; top of a doubleton; K from AK.
   One or two sentences, assertive (the leader sees their own hand).

2. `[ROLE declarer][STAGE auction-end]` — the plan BEFORE the lead: state the
   contract, count the sure winners (or losers in a suit contract), name the
   problem the theme poses, and the line. 2-4 sentences.
   **REQUIRED:** include one sentence reading the OPPONENTS from the auction —
   the exact HCP complement and, when `silent`, what the silence rules out:
   "NS hold 24 of the 40, so the defence has only 16 — and with neither
   opponent bidding, no one is hiding a long suit or a big hand, so the points
   and the missing honours rate to be split." When an opponent DID bid, read
   that instead (length/strength shown). This sets up the placement read that
   the post-lead tip then completes.

3. `[ROLE declarer][STAGE post-lead]` — fires AFTER the opening lead, so START
   from the actual lead: name what was led, the trick-1 decision (win / duck /
   which card), and what the lead suggests — but HEDGE the read (the card is a
   fact, its meaning an inference): "the \D2 looks like a fourth-best,
   suggesting about four" / "looks like top of a sequence, so West probably
   holds the QJ" / "looks like a singleton — watch for a ruff." Then walk the
   technique to the contract. 3-5 sentences.
   **REQUIRED — state the inference, WITHHOLD the conclusion.** This tip must
   turn the available evidence into a PLACEMENT read, not a bare "the missing
   honours are split somewhere." Combine (a) the lead, (b) the auction/silence,
   and (c) vacant spaces to say WHERE the key card the technique targets rates
   to sit — then STOP. Do NOT append the resulting line. Give the read and let
   the student draw the play conclusion:
   - GOOD: "West led from club length and neither opponent could act, so the
     long clubs — and the room for the missing \HK — probably sit with West."
   - HEDGE THE LENGTH READ TOO: a fourth-best lead only *suggests* length
     (it can be from four or five, and leads vary), so write "probably sits
     with West" / "looks like West's length", never "the length sits with
     West" as fact. Hedge both the length inference and the honour placement.
   - BAD (hands the answer): "...so the \HK sits with West, so finesse through
     West / lead low to the queen." Drop everything from "so finesse…" on.
   This is the single most important opponent-inference beat; never skip it on
   a finesse or placement board. Keep it hedged ("rates to", "more likely",
   "looks like") — never state a defender's card as fact, and never tack on the
   technique that follows from it.

4. `[ROLE declarer][STAGE post-play]` — the review: what mattered, why the
   technique worked, and PRAISE (this is the safe place for warmth). 2-3
   sentences.

(For defense scenarios add `[ROLE defender][STAGE post-lead]` from the
defender's vantage; same hedging rules.)

## Use the verified trick_map — do NOT count tricks yourself

Each packet board carries a `trick_map` computed by exact double-dummy from
the known cards (`py/suit_tricks.py`). This exists because counting tricks by
eye is where generated coaching slips (e.g. calling a KQJ-plus-length suit
"four tricks" when it is three, and missing the real source). Treat it as
ground truth:

```
"trick_map": {
  "suits": { "S": {"top": 0, "establishable": 3, "ns_len": 7},
             "H": {"top": 1, "establishable": 1, ...},
             "D": {"top": 3, "establishable": 3, ...},
             "C": {"top": 0, "establishable": 4, ...} },
  "development_suit": "C"
}
```

- `top` = tricks NS cash immediately (consecutive top honours from the ace).
- `establishable` = tricks in that suit after forcing out the opponents'
  higher honours (with entries) — the realistic count once set up.
- `development_suit` = the suit yielding the most NEW tricks; this is normally
  where the ninth trick comes from. NAME THIS SUIT as the one to develop.

Rules: state trick counts ONLY from `establishable`/`top`. When you describe
developing a suit for extra tricks, it must be the `development_suit` (or a
suit whose `establishable` exceeds its `top`); never tell declarer to develop
a flat suit. Your running count must reconcile with the contract — if your
narrative sums to fewer than the tricks needed, you have the wrong suit.

### Suit contracts: the trump-aware trick_map (`py/trump_tricks.py`)

For a **suit** contract the packet's `trick_map` is the trump-aware shape below
(the NT `suits`/`development_suit` map is wrong once there are trumps — winners
get ruffed and extra tricks come from ruffing, not only length):

```
"trick_map": {
  "trumps": "S", "declarer": "S", "dummy": "N",
  "total": 10, "dd_losers": 3,            // AUTHORITATIVE (exact DD) — reconcile to these
  "trump_suit": { "ns_len": 9, "decl_len": 5, "dummy_len": 4,
                  "long_hand": "S", "short_hand": "N", "short_len": 4,
                  "isolated_tricks": 5,   // trump tricks if drawn (exact)
                  "missing_honors": ["T"] },
  "side_suits": { "H": {"top":0,"safe_top":0,"establishable":1,"length_winners":1,
                        "decl_len":3,"dummy_len":1,"short_hand_ruffs":2,
                        "missing_honors":["A","K","J","T"]}, ... },  // excludes trump
  "side_top": 1,                 // side winners cashable before a defender can ruff
  "ruffs_in_short_hand": 2,      // extra ruffing tricks the SHORT trump hand can make
  "sure_tricks": 6, "develop": 4 // floor and the tricks still to find
}
```

- **EXACT — state as fact:** `total` (declarer's double-dummy trick count —
  your narrative must reconcile to it and NEVER claim more), `dd_losers`
  (= 13 − total), each side suit's `top`/`establishable`, and the trump suit's
  `isolated_tricks`. `missing_honors` are the outstanding honours — use them to
  read finesse/drop positions, but HEDGE placement (you can't see the defenders'
  cards).
- **PLANNING AIDS — guide the plan, don't quote as a second trick source:**
  `sure_tricks` (a floor), `develop` (= total − sure_tricks), and
  `ruffs_in_short_hand`. For a **ruff-in-dummy** lesson, the headline is
  `ruffs_in_short_hand` and the side suit whose `short_hand_ruffs` is the source
  — tell declarer to ruff those losers in the SHORT trump hand BEFORE drawing
  trumps. For **establish-long-suit** / suit-promotion, the source is the side
  suit whose `length_winners` is largest. For finesse/drop lessons the verified
  finesse value is already baked into `establishable`/`isolated_tricks` (the
  analyser is seat-aware) — coach the technique, hedge the honour placement.
- `safe_top` ≤ `top`: a top winner is at risk of a ruff when a defender is short
  in the suit. Prefer `safe_top` when telling declarer what they can cash early.

The discipline is the same as notrump: count from the verified numbers, and the
running plan must reconcile to `total`.

## Use the verified defender_budget — do NOT count the defenders by eye

Each packet also carries a `defender_budget` (`py/defender_budget.py`) — what
declarer can KNOW and INFER about the two HIDDEN hands. It is the HCP/shape
counterpart of `trick_map`: reasoning about the defenders by eye slips the same
way counting tricks does (over-stating a defender's hand, mis-placing the
missing honours, botching the rule-of-11). Narrate these numbers; don't derive
them.

```
"defender_budget": {
  "ns_hcp": 24, "defender_hcp": 16,        // EXACT (declarer + dummy known)
  "defenders": { "lho": {"seat":"W","hcp":6,"shape":[5,1,4,3],"longest":5},
                 "rho": {"seat":"E","hcp":10,"shape":[2,5,3,3],"longest":5} },
  "silent": true,                          // both defenders passed -> couldn't act
  "rule_of_11": { "suit":"S","card":"4",   // only on a 4th-best length lead; else null
                  "higher_outside":7, "higher_in_ns":5, "higher_in_hidden":2 }
}
```

- `ns_hcp` / `defender_hcp` are **EXACT and known** once dummy is down (declarer
  + dummy are a fixed count; the defence shares the rest of 40). State them as
  fact. The natural beat in `[STAGE auction-end]`: *"NS hold 24 of the 40, so
  the defence has only 16 between them — and since neither opponent bid, no one
  is hiding a long suit or a big hand."* Drop the silence clause when `silent`
  is false.
- The **per-defender split** in `defenders` is an INFERENCE. You may use the
  true `hcp`/`shape` to point the read the right way, but the prose MUST hedge
  it (same rule as reading defenders' cards): *"the missing 16 are split, and
  West led from length, so East rates to hold the outstanding aces."* Never name
  which defender holds a specific honour as fact.
- `rule_of_11` (present only on a 4th-best length lead vs NT) gives the exact
  placement: `higher_in_hidden` = cards above the led card in the LEADER'S
  PARTNER'S hand. Use it in `[STAGE post-lead]`: *"by the rule of eleven, two
  cards higher than the four sit outside dummy and my hand — both with East."*

**Mandatory floor (every board, every difficulty):** the auction-end tip states
the exact HCP complement and, when `silent`, the silence read; the post-lead tip
turns the lead + auction + vacant spaces into a hedged PLACEMENT read for the
card the technique targets. These are not optional colour — a play tip that
names a finesse without saying which defender it rates to beat is incomplete.

Gate the EXTRA depth by `difficulty`: the rule-of-eleven count and explicit
vacant-spaces arithmetic ("East has more room, so the queen rates to be there")
are for difficulty >= 2; at difficulty 1 keep the placement read to a plain
hedged sentence. Keep every defender read hedged regardless.

## Hard rules

- The pre-lead card is load-bearing and the trainer AUTO-PLAYS it. Each packet
  board provides the authoritative `opening_lead` (e.g. `\H6`) computed from
  the leader's hand — use THAT card verbatim in the `Lead the \Xr` sentence.
  Do not pick your own (a KQxxx without the J/T leads 4th-best, not the K).
  Written `\Xr`, no space. `play-splice` cross-checks it and warns on mismatch.
- Tips are written from ONE role's vantage and only mention what that role can
  see at that stage. The leader tip sees only the leader's hand; the declarer
  auction-end tip sees declarer + dummy (dummy is down after the lead for
  post-lead). Do NOT reveal a hand the role can't see.
- HEDGE declarer's reads of the defenders' cards (inferences, not facts).
- Defensive signals (attitude/count/suit-preference): NUANCED and OPTIONAL —
  the audience is beginner/senior and rarely signals reliably. Never state a
  signal as fact; hedge ("if they're signaling, that high card hints at…, but
  don't count on it"). Prefer concrete card-reading (rule of 11, who showed
  out) over signal theory.
- Suit escapes `\S \H \D \C` render as ♠♥♦♣.
- The winning line must be findable by PRINCIPLE (counting, the named
  technique), not double-dummy. The board was curated so the principled line
  succeeds and a careless line fails.

## Pipeline (parallels coach.py)

1. `coach.py play-packets <scenario>` — select curated boards for the theme,
   build packets {board, deal (all four hands, for the AUTHOR to reason about
   the play), contract, declarer, leader, theme, curate note, dd info}.
2. A subagent per packet writes the tips per this spec.
3. `coach.py play-splice <scenario>` — splice the tips after each board's
   auction; validate (pre-lead card present + no-space, [ROLE]/[STAGE] parse,
   endplay-parses).

## Interactive play decisions — the `[PLAY]` marker (live)

The trainer now supports an interactive per-decision play quiz that mirrors the
bidding quiz: at an authored decision it presents coaching, lets the student
click a card, praises a correct card, coaches + retries a wrong one, and after a
second miss explains the right play and plays it. Between decisions the trainer
auto-plays every seat (declarer, dummy, defenders) so the hand reaches each
decision on its own — the student only acts at the meaningful moments.

Author decisions with `[PLAY]`, placed AFTER the four `[ROLE]/[STAGE]` tips, in
the same post-`[Auction]` `{ ... }` block:

```
[PLAY <trick> <seat> <card>]
  ...PRESENT prose — set the scene and ask the question; WITHHOLD the answer
  (same "don't state the conclusion" rule as the post-lead tip)...
[ACCEPT <card> ...]            (optional — co-correct cards)
[WHY]
  ...WHY prose — names the card and explains; shown on a correct answer AND as
  the explanation after the second miss, so it MAY state the conclusion...
```

- `<trick>` = 1-based trick number the decision fires on. `<seat>` = the student
  seat that must be on play in REAL compass (`N`/`S` for a declarer lesson — it
  disambiguates declarer vs. dummy). `<card>` = the correct card as `\HQ`.
- Anchor on a decision the engine's auto-play line actually reaches; the trainer
  drops (skips) a decision it can't reach, so verify the line. Quiz only the 1–3
  genuinely meaningful decisions — never routine follows.

Worked example (Finesse_Simple board 44 — the heart finesse):

```
[PLAY 6 S \HQ]
Here is the heart position the whole hand has been about. Dummy leads the \H9
toward your hand, East follows low, and you hold \HA Q 7 with the king still
out. Which heart do you play?
[WHY]
Play the \HQ — the finesse. East followed low, so the king rates to sit under
your A-Q just where you want it; the queen drives it out or wins outright, and
the ace takes care of the rest. Banging down the \HA instead would crash an
honour and hand the defence a trick with the king.
```

Boards with no `[PLAY]` markers play exactly as before (manual, no quiz).
