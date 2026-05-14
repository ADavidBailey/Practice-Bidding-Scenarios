# Note to Rick — deploying the Bridge Play Trainer

Hi Rick,

Here's what Claude suggested I sen to you:

I've been building a **Bridge Play Trainer** alongside the PBS work — a web
app that lets a player practice the *play* of the hand (declarer or defender)
on deals from the PBS scenarios, with optional Claude grading of the
player's reasoning about the hidden hands after each trick. It's working
locally and I'd like to make it available to bridge all bridge players.

I'd appreciate your read on the best way to host it.  I think it would make
a nice addition to your Bridge Classroom.  Claude suggested some other options.

## What it is

- Frontend: plain HTML/CSS/JS, no framework, no build step.
- Backend: FastAPI (Python) using `endplay` for PBN parsing + double-dummy
  solving. Reads PBN files from `bba/` for the deal source. ~600 lines.
- Optional Claude grading: the user's API key lives only in their browser
  (localStorage), and the browser calls Anthropic directly with the
  `anthropic-dangerous-direct-browser-access` header. The server never sees
  the key.
- Source lives in `bridge-play-trainer/` in the PBS repo.

## Why I can't just put it on GitHub Pages like the PBS Dashboard

The dashboard is pure static HTML + JSON. The trainer needs the FastAPI
server running because every card play goes through DDS to compute legal
moves and pick computer plays. Porting DDS to the browser via WASM would
work but is a project of its own.

## The deployment options I see

1. **Free PaaS (Render, Fly.io, Railway) + static frontend on GH Pages.**
   Server auto-deploys from the repo on push. Free tiers spin down after
   inactivity (~30 s cold start). I'd put the frontend on GitHub Pages
   pointed at the PaaS URL. Cheapest, simplest. ~1 evening to set up.

2. **Always-on small VPS.** Hetzner, DigitalOcean, ~$5/mo. No cold starts.
   I'd run uvicorn behind nginx + a TLS cert. More fiddly to maintain.

3. **Package as a desktop app** (PyInstaller / Electron). One-click install
   but several days of work plus code-signing.

For a small bridge-club audience, (1) seems right. The 30-second cold start
on first visit is annoying but tolerable for a teaching tool.

## What I'm asking

- Have you deployed FastAPI apps on Render/Fly/Railway? Which one would you
  pick for something like this?
- Anything you'd watch out for given that the trainer holds per-session
  state in memory (each user gets a `Session` keyed by a random token)?
- Worth bundling the PBN files into the image, or pulling them at startup
  from the GitHub repo?
- Would it ever make sense to host the trainer next to your `bba-cli`
  infrastructure (since they share Python deps and PBN appetite)?

Happy to walk through the code if useful. The interesting bits are
[`bridge-play-trainer/server.py`](bridge-play-trainer/server.py) and the
`Session` class.

## How to try it locally

From a checkout of `ADavidBailey/Practice-Bidding-Scenarios`:

```bash
pip3 install endplay fastapi uvicorn
python3 -m uvicorn bridge-play-trainer.server:app --reload --port 8765
```

Then open <http://localhost:8765/> in a browser. Pick a scenario from the
sidebar (e.g. **Major Suit Fit**), choose **Play as: Declarer / Leader /
Defender**, click **Play** to dismiss the bidding box, and click cards to
play. Undo / Replay / Claim / Next deal are all on the picker bar.

Claude grading is optional. Without a key, the trainer is just a play
trainer with no inference grading. To turn grading on, click the ⚙ icon →
**Set up key…** and walk through the wizard (the wizard explains where to
get an Anthropic API key — $5 of credit lasts hundreds of deals; your key
stays in your browser).

Thanks,
David
