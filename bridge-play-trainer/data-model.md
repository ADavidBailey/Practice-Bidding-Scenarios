# Data Model & API Contracts — Bridge Play Trainer

This is the **internal data structure** the trainer uses, plus the **HTTP API** between frontend and backend (once we wire up a web stack).

## Core types

### Card

```json
{
  "suit": "S",        // S, H, D, C
  "rank": "A"         // A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2
}
```

### Hand

```json
{
  "spades":   ["A", "K", "Q", "5", "4"],
  "hearts":   ["A", "8"],
  "diamonds": ["K", "7", "2"],
  "clubs":    ["J", "6", "3"]
}
```

### Deal

```json
{
  "deal_id": "Major_Suit_Fit#42",
  "scenario": "Major_Suit_Fit",
  "deal_index": 42,
  "dealer": "S",
  "vulnerability": "None",          // None | NS | EW | All
  "hands": {
    "N": { ... Hand ... },
    "E": { ... Hand ... },
    "S": { ... Hand ... },
    "W": { ... Hand ... }
  }
}
```

### Auction

```json
{
  "dealer": "S",
  "calls": [
    { "seat": "S", "call": "1S" },
    { "seat": "W", "call": "Pass" },
    { "seat": "N", "call": "3S" },
    { "seat": "E", "call": "Pass" },
    { "seat": "S", "call": "4S" },
    { "seat": "W", "call": "Pass" },
    { "seat": "N", "call": "Pass" },
    { "seat": "E", "call": "Pass" }
  ],
  "final_contract": {
    "level": 4,
    "strain": "S",                  // S, H, D, C, NT
    "declarer": "S",
    "doubled": 0                    // 0=undoubled, 1=X, 2=XX
  }
}
```

### Trick

```json
{
  "trick_number": 3,                // 1-13
  "leader": "S",
  "plays": [
    { "seat": "S", "card": { "suit": "S", "rank": "5" } },
    { "seat": "W", "card": { "suit": "S", "rank": "6" } },
    { "seat": "N", "card": { "suit": "S", "rank": "K" } },
    { "seat": "E", "card": { "suit": "S", "rank": "3" } }
  ],
  "winner": "N",
  "trump_break": null               // populated if all trumps now drawn
}
```

### Play state

```json
{
  "deal_id": "...",
  "auction": { ... },
  "tricks_completed": [ ... Trick ... ],
  "current_trick": {                // null between tricks
    "leader": "N",
    "plays": [ ... partial ... ]
  },
  "user_role": "declarer",           // declarer | defender_E | defender_W
  "user_seat": "S",
  "user_visible_hands": ["S", "N"],  // for declarer; ["W"] only for defender_W
  "tricks_taken": { "NS": 5, "EW": 2 }
}
```

### User-visible state (sent to frontend per turn)

```json
{
  "play_state": { ... above ... },
  "hands_known": {                   // only what user can see
    "S": { ... full Hand ... },
    "N": { ... full Hand ... },
    "E": null,
    "W": null
  },
  "cards_played_by_seat": {          // computed view: what each seat has played
    "S": ["S5", "HA"],
    "W": ["HK", "S6"],
    "N": ["S2", "SK", "H7"],
    "E": ["H2", "S3"]
  },
  "expected_action": {
    "type": "play_card",             // play_card | inference_prompt | scenario_pick
    "seat_to_play": "S",
    "input_mode": "free_text"        // free_text | structured | none
  }
}
```

### Inference (user input)

#### Free-text mode

```json
{
  "deal_id": "...",
  "trick_number": 3,
  "mode": "free_text",
  "estimate": {
    "free_text": "West has ♥KQJ + one small heart. About 9–11 HCP. East passed twice — likely under 12 HCP. East's ♥2 was discouraging."
  }
}
```

#### Structured mode

```json
{
  "deal_id": "...",
  "trick_number": 5,
  "mode": "structured",
  "estimate": {
    "W": { "lengths": { "S": 2, "H": 4, "D": 4, "C": 3 }, "hcp": 10 },
    "E": { "lengths": { "S": 2, "H": 5, "D": 3, "C": 3 }, "hcp": 5 }
  }
}
```

### Inference evaluation (response from Claude)

```json
{
  "trick_number": 3,
  "grade": {
    "overall": "good",               // excellent | good | partial | poor
    "score": 0.75,                   // 0.0 - 1.0
    "by_facet": [
      { "facet": "♥KQJ in West",  "result": "correct", "note": "Top-of-sequence lead reliably shows two touching honors below." },
      { "facet": "West's HCP",      "result": "correct", "note": "8-11 HCP estimate plausible." },
      { "facet": "West's heart length", "result": "missed", "note": "With KQJ + 4 hearts, West would have overcalled 2♥. Pass suggests exactly 4 hearts." },
      { "facet": "East's signal",   "result": "correct", "note": "Correctly read discouraging attitude on ♥2." }
    ]
  },
  "trainer_analysis": "Your read of West's heart honors is solid. The big inference you missed is that West has exactly 4 hearts (not 4+), since with 5 hearts they would have overcalled 2♥.",
  "next_trick_hint": "Watch East's count signal in spades. East's first spade card may indicate odd/even length."
}
```

### Deal summary (end of deal)

```json
{
  "deal_id": "...",
  "final_contract": "4S by S",
  "tricks_taken": { "NS": 10, "EW": 3 },
  "result": "+420",
  "inferences_summary": {
    "total": 8,
    "correct": 5,
    "partial": 1,
    "missed": 2,
    "score_pct": 63
  },
  "lessons": [
    "When 3 of a defender's suits are constrained, the 4th is determined.",
    "Top-of-sequence leads (♥K from ♥KQJ) telegraph 2 touching honors below."
  ]
}
```

## HTTP API (between frontend and backend)

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/api/scenarios` | List available scenarios |
| `POST` | `/api/session` | Start session: pick scenario, mode, options. Returns first deal. |
| `GET`  | `/api/session/{id}/state` | Get current visible state |
| `POST` | `/api/session/{id}/play` | Play a card |
| `POST` | `/api/session/{id}/inference` | Submit user's read for current trick |
| `POST` | `/api/session/{id}/next_deal` | Move to next deal in scenario |
| `DELETE` | `/api/session/{id}` | End session |

### Example: start session

`POST /api/session`
```json
{
  "scenario": "Major_Suit_Fit",
  "mode": "play",                    // play | defend | both
  "signaling": {
    "attitude": "standard",          // standard | upside_down
    "count": "standard",
    "suit_preference": "lavinthal"   // lavinthal | mckenney | off
  },
  "opening_lead": "human_heuristic", // human_heuristic | dds_optimal | random
  "input_mode": "auto"               // auto = free_text first 3 tricks, structured after | free_text | structured
}
```

Response:
```json
{
  "session_id": "abc-123",
  "deal_id": "Major_Suit_Fit#42",
  "play_state": { ... },
  "hands_known": { ... },
  "auction": { ... },
  "expected_action": { ... }
}
```

### Example: play a card

`POST /api/session/abc-123/play`
```json
{ "card": { "suit": "S", "rank": "A" } }
```

Response: updated state. If trick completes, backend auto-plays remaining defender cards via DDS, returns next prompt.

### Example: submit inference

`POST /api/session/abc-123/inference`
```json
{
  "mode": "free_text",
  "estimate": { "free_text": "West has ♥KQJ..." }
}
```

Response: `InferenceEvaluation` (see above).

## Backend internal modules

```
bridge-play-trainer/
├── data-model.md          # this file
├── wireframe.md           # UI mockup
├── pipe1.py               # current MVP: standalone deal walker
├── server.py              # FastAPI server (deferred until web stack chosen)
├── engine/
│   ├── __init__.py
│   ├── deal.py            # load deal from pbn, model state
│   ├── play.py            # state machine for play
│   ├── dds.py             # endplay wrapper for DDS card-pick
│   ├── signals.py         # signaling-style card-selection layer
│   └── claude.py          # API client for inference evaluation
└── tests/
    └── ...
```

## Open design questions

- **Inference timing**: prompt after each trick or only at trick boundaries the user opts into? MVP: after each trick.
- **Signal calibration**: when DDS picks ties, which signaling rule breaks them? Hard-coded mapping per signal style.
- **Multi-deal sessions**: store cumulative stats across deals? MVP: per-deal only.
