# Layer B pilot — Basic_NT grading report

500 boards from `bba/Basic_NT.pbn` graded by 5 parallel subagents against
the rubric in pbn-curation-plan.md. Verdicts: `bba-curated/Basic_NT-graded.json`.

## Tier counts

| discipline | textbook | standard | judgment | reject |
|---|--:|--:|--:|--:|
| bidding | 302 | 107 | 57 | 34 |
| declarer | 10 | 270 | 6 | 214 |
| defense | 4 | 257 | 20 | 219 |

Auction classes: {'intended': 456, 'interference': 21, 'bba-disagreed': 10, 'continuation': 13}
Declarer themes: {'count-winners': 172, 'finesse-basic': 67, 'establish-long-suit': 40, 'danger-hand': 3, 'timing': 2, 'hold-up': 2}
Defense themes: {'opening-lead-nt': 247, 'passive-defense': 18, 'hold-up-ace': 5, 'opening-lead-suit': 5, 'count-declarers-tricks': 3, 'duck-to-keep-communication': 1, 'lead-partners-suit': 1, 'cash-out': 1, 'return-partners-suit': 1}

## Regex-reject yield (the bba/ vs bba-filtered question)

Of the 40 boards the regex rejected:

- **interference**: 18 boards, 13 usable for bidding
- **bba-disagreed**: 10 boards, 0 usable for bidding
- **continuation**: 12 boards, 0 usable for bidding

Plus 4 regex *false positives* — matched the pattern but the
auction is actually off-script (the regex matches a prefix, so it misses
back-in interference after 1N-Pass-Pass).

## Spot-check sample (please review these ~10)

### Board 1 — intended, dd ok, difficulty 1
- bidding: **textbook** — Clean 17 balanced, N's 7-count pass matches the table exactly.
- declarer: **reject** — 9 tricks in 1N, two overtricks regardless — nothing to teach.
- defense: **reject** — Declarer has comfortable overtricks whatever defense does.

### Board 430 — intended, dd down_both, difficulty 2
- bidding: **reject** — South passed the 2NT invite holding 17 — a maximum must always accept; indefensible as an answer key (and North's 7-count invite was also off-table).
- declarer: **reject** — down_both — 6 tricks max, down two in 2NT.
- defense: **standard** themes=['opening-lead-nt'] — East's fourth-best spade from AQ952 powers a two-trick set.

### Board 249 — intended, dd down_both, difficulty 3
- bidding: **reject** — N raised to 3N with a flat quacky 9 (KT2 KQ2 J864) — table says invite; contract down two confirms the overbid.
- declarer: **reject** — 7 tricks max.
- defense: **standard** themes=['opening-lead-nt'] — W's 4th-best diamond from AT975 sets up the beat with E's club AK.

### Board 81 — interference, dd down_both, difficulty 2
- bidding: **standard** — E-W balanced to 2S after 1N-P-P; N's 6-count pass and S's quiet defense are fine, but the final contract belongs to the opponents (matched_intended flag is misleadingly true).
- declarer: **reject** — Opponents declare 2S — no N-S declarer play to grade.
- defense: **reject** — 2S is down three regardless — no key defensive decision, and suit defense is off this lesson.

### Board 389 — intended, dd down_both, difficulty 2
- bidding: **standard** — 16 opposite 10 — 3N per table, but one down DD; correct bidding, sour ending, capped at standard.
- declarer: **reject** — Contract fails double-dummy (8 tricks).
- defense: **textbook** themes=['opening-lead-nt'] — W's 4th-best heart from AQ873 sets up and beats 3N — the classic lead-your-long-suit lesson with a payoff.

### Board 112 — intended, dd ok, difficulty 3
- bidding: **judgment** also_ok=['3N'] — S passed the 2N invite with a prime 16 (AQ5 AK7) and 9 tricks were there — accepting with a good 16 is at least as defensible.
- declarer: **standard** themes=['count-winners'] — 9 tricks dd in 2N; one-trick cushion, straightforward development.
- defense: **reject** — 2N always makes; only an overtrick at stake.

### Board 319 — intended, dd down_both, difficulty 2
- bidding: **reject** also_ok=['2N'] — N has 9 HCP — the brief's table says 2N invitational, not 3N; the leap to a failing game (down 2 DD) is not defensible as an answer key.
- declarer: **reject** — 3N is down two double-dummy.
- defense: **standard** themes=['opening-lead-nt'] — Defenders take 3N down two with normal leads and development.

### Board 23 — bba-disagreed, dd ok, difficulty 2
- bidding: **reject** — Robot used 4C Gerber relay; brief says N's 16-count bids a direct quantitative 4N — conventional auction unusable as a no-conventions answer key.
- declarer: **reject** — 12 tricks in 4N — two overtricks, nothing to teach.
- defense: **reject** — Overtricks regardless.

### Board 417 — interference, dd down_both, difficulty 3
- bidding: **judgment** also_ok=['X'] — West's 2H overcall buys it; South's pass with 16 is timid (reopening double is normal) but defensible in a beginner no-convention setting — off-lesson board.
- declarer: **reject** — Opponents declare 2H — no declarer lesson for the student side.
- defense: **standard** themes=['passive-defense'] — NS hold 23 HCP and beat 2H three tricks with routine passive defense.

### Board 137 — intended, dd ok, difficulty 3
- bidding: **judgment** also_ok=['2N'] — N bid 3N with 9 HCP — table says 2N invite; AQT6 with tens makes the upgrade arguable, and it makes exactly.
- declarer: **standard** themes=['finesse-basic'] — Exactly 9 dd; the club finesse through W is a key trick.
- defense: **standard** themes=['opening-lead-nt'] — E's red-suit honors over declarer hold the total to 9.

