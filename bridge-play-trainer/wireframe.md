# UI Wireframe — Bridge Play Trainer

Plain HTML/CSS rendering target. Not photorealistic — just functional. The "fancy" version comes later.

## Layout (declarer mode)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Bridge Play Trainer                          Scenario: Major_Suit_Fit · #42 │
│                                                          Deal 3 of session  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ AUCTION                                                                │  │
│  │       W       N       E       S                                        │  │
│  │       —       —       —       1♠                                       │  │
│  │     Pass     3♠     Pass     4♠                                        │  │
│  │     Pass    Pass    Pass                                               │  │
│  │                                                                        │  │
│  │ Contract: 4♠ by South · Vul None                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                       │   │
│  │              ┌─── North (dummy) ───┐                                  │   │
│  │              │  ♠  K 9 8 2          │                                 │   │
│  │              │  ♥  9 7              │                                 │   │
│  │              │  ♦  A J 8 5          │                                 │   │
│  │              │  ♣  Q 7 4            │                                 │   │
│  │              └─────────────────────┘                                  │   │
│  │                                                                       │   │
│  │  ┌─── West ───┐         ┌─── Current Trick ───┐     ┌─── East ───┐    │   │
│  │  │  (hidden)   │         │       N             │     │  (hidden)   │   │
│  │  │             │         │  ♥9           ?    │     │             │   │
│  │  │  Played:    │         │ W       E          │     │  Played:    │   │
│  │  │  ♥K  ♠6     │         │       ?            │     │  ♥2  ♠3     │   │
│  │  │             │         │       S            │     │             │   │
│  │  │             │         │                    │     │             │   │
│  │  │ HCP est: 9  │         │ Trick 3 of 13      │     │ HCP est: 5  │   │
│  │  │ ♠2 ♥4 ♦4 ♣3│         │ NS: 2 · EW: 0      │     │ ♠2 ♥5 ♦3 ♣3│   │
│  │  └─────────────┘         └────────────────────┘     └─────────────┘    │
│  │                                                                       │   │
│  │              ┌─── South (you) ─────┐                                  │   │
│  │              │  ♠  A Q J 5 4        │                                 │   │
│  │              │  ♥  A 8              │                                 │   │
│  │              │  ♦  K 7 2            │                                 │   │
│  │              │  ♣  J 6 3            │                                 │   │
│  │              └─────────────────────┘                                  │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─── INFERENCE PANEL ──────────────────────────────────────────────────┐  │
│  │                                                                       │   │
│  │  After trick 2, what's your read on West and East?                    │   │
│  │                                                                       │   │
│  │  [Free-text input area — will switch to structured form at trick 4]   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │ West has ♥KQJ — top of sequence. Probably 4 hearts since pass.  │  │   │
│  │  │ 9–11 HCP. East's ♥2 was discouraging.                            │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                       │   │
│  │  [Submit Inference]   [Skip and Play]                                 │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─── TRAINER FEEDBACK ─────────────────────────────────────────────────┐  │
│  │                                                                       │   │
│  │  ✅ ♥KQJ correctly inferred — top-of-sequence lead reliably shows...│   │
│  │  ✅ West's HCP ceiling — passing rules out 2-level overcall...      │   │
│  │  ⚠️ Heart length — with KQJ + 4 hearts West would have overcalled.. │   │
│  │  ✅ East's signal — correctly read discouraging.                    │   │
│  │                                                                       │   │
│  │  🎯 Next trick: Watch East's first spade card for count signal.       │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key UI elements

### Auction panel (top)
- Standard auction display: 4 columns (W/N/E/S), one row per round.
- Final contract + vulnerability summary below.
- Static once the auction is set.

### Bridge table (middle)
- Diamond/cross layout with N at top, S at bottom, W left, E right.
- Hidden hands show **"Played"** strip with cards each defender has revealed.
- Current trick area in the center: 4 slots for the 4 cards as they're played.
- Trick counter + NS/EW trick counts displayed prominently.
- **HCP estimate + length estimates** appear next to each hidden hand once the user submits them. Updated each trick.

### Inference panel (below table)
- Prompt question at top.
- Free-text area OR structured form (5 inputs per defender: 4 lengths + HCP).
- Toggle button to switch modes manually (user choice override).
- Submit + skip buttons.

### Trainer feedback panel (bottom)
- Persistent: shows feedback from previous inference.
- Replaces with new feedback when user submits.
- Color-coded: ✅ correct, ⚠️ missed, ❌ wrong, 💡 hint, 🎯 next-trick.

## Settings panel (modal)

Triggered from settings icon (gear):

```
┌─── Session Settings ───────────────────────────────┐
│                                                     │
│  Scenario:       [Major_Suit_Fit ▼]                 │
│  Mode:           ○ Play ● Defend ○ Both            │
│  Signaling:                                         │
│    Attitude:    [Standard ▼]                       │
│    Count:       [Standard ▼]                       │
│    Suit Pref:   [Lavinthal ▼]                      │
│  Opening Lead:  [Human heuristic ▼]                │
│  Input Mode:                                        │
│    [Auto: text → structured at trick 4 ▼]          │
│                                                     │
│  Grading:                                           │
│    ● Show me the real hands at end of deal         │
│    ○ Auto-check my numbers (free)                  │
│    ○ Claude grades my reasoning  [Walk me through] │
│                                                     │
│  [Apply]  [Cancel]                                  │
└─────────────────────────────────────────────────────┘
```

### Claude-grading setup wizard

Triggered by the "Walk me through" button. One screen at a time, big "Next" and "Cancel" buttons, no jargon.

**Step 1 — What this does**
> Claude reads your guesses about the hidden hands and explains where your reasoning is sharp and where it's off. About a penny per deal. You can turn it off anytime.

**Step 2 — Open Anthropic's website**
> Click the button below. It will open Anthropic's website in a new tab. Sign in, or click "Sign up" if you've never been there.
>
> **While you're there**, set a small monthly spending cap (we suggest $5) so the trainer can't accidentally overspend. The setting is under **Billing → Usage limits**.
>
> [ Open Anthropic Console → ]
>
> When you're back, click Next.

**Step 3 — Get your key**
> On the Anthropic website:
> 1. Click "API Keys" in the left sidebar
> 2. Click "Create Key"
> 3. Copy the long string that appears (it starts with `sk-ant-`)
>
> Paste it here:
> [_______________________________________]
>
> [ Test & Save ]

If the key fails the test call: "That doesn't look right — try copying it again. The key should start with `sk-ant-`."

**Step 4 — All set**
> Working! Claude grading is now on. You can turn it off anytime in settings.

### Where the key lives

- **Browser only** (localStorage). Never sent to our server. If the user switches browsers or clears site data, they re-paste it.
- The browser calls Anthropic directly (or via a thin pass-through that doesn't log the key) so we never see it.
- The settings panel shows the key as `sk-ant-…••••` once stored, with a "Remove key" button.

## Card playing

- User clicks their card to play it (drag-drop is overkill for MVP).
- Dummy's turn: user clicks dummy's card (declarer controls both).
- Defender's turn: backend plays via DDS, UI updates after a brief delay.
- Trick completes: cards animate to winner's "tricks taken" pile, current trick clears.

## Defender mode adjustments

When user is defender (E or W):
- Their own hand visible.
- Other 3 hands hidden (including partner!).
- "Played" strips next to all three hidden hands.
- Inference prompts: "What's your read on declarer (S) and dummy (N) — and your partner's hand?"
- Card-play: user picks own card; backend plays declarer, dummy, partner via DDS.

## End-of-deal screen

```
┌─── Deal Complete ─────────────────────────────────────────────────┐
│                                                                     │
│  Contract: 4♠ by S    Result: Made 10 (+420)                       │
│                                                                     │
│  Inference Summary:    5/8 correct (63%)                            │
│                                                                     │
│  Highlights:                                                        │
│    ✅ Read ♥KQJ from top-of-sequence lead                          │
│    ✅ Spotted East's discouraging signal                            │
│    ❌ Missed inference that W had exactly 4 hearts                  │
│    ❌ Got ♦ split wrong at trick 7                                  │
│                                                                     │
│  Lesson: When 3 of a defender's suits are constrained, the 4th    │
│  is determined. Watch for the moment to lock down distributions.   │
│                                                                     │
│  [Next Deal]   [End Session]   [Review This Deal]                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Implementation notes

- **Single page app**. No navigation between pages — modal for settings, in-page state for everything else.
- **No login** for MVP. Session ID in URL or localStorage.
- **Mobile responsive** is post-MVP. Desktop only initially.
- **Card display**: use Unicode suit symbols (♠♥♦♣) + ranks. No card images.
- **Animations**: nice but optional. CSS transitions on trick collapse.
