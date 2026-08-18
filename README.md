# Creator Signal Prototype

A working prototype for a talent agency's Head of Creative Partnerships: given a batch of TikTok
video data, which creators and content look most promising, and why should she trust the answer?

Two screens:

1. **At a glance summary** (`/`) — a ranked list of promising creators, computed from the data.
2. **Q&A chat** (`/chat`) — ask natural-language questions and get answers that are either
   computed from real data or clearly labeled as AI opinion.

## What "promising" means, and why

A creator is **promising** if:

- Their total views across the batch fall between **250,000 and 10,000,000**.
- Ranked by **average per-video engagement rate** — `(likes + comments + shares) / views`,
  averaged across their videos in the batch.

This definition was chosen after testing the alternatives against the real dataset (see
`docs/brainstorms/2026-08-17-creator-signal-prototype-requirements.md` for the full walkthrough):

- **Reach alone** surfaces already-massive accounts (a global pop star with 250M views on one
  video) — not realistic recruit or brand-pitch targets, since they're already famous.
- **Engagement rate alone** surfaces 1-video accounts with a few hundred views and a lucky
  ratio — noise, not signal.
- **Floor + ceiling + rate together** avoids both failure modes: it excludes celebrity-tier
  reach, filters out statistical noise, and ranks the rest by genuine audience connection.

Applied to this dataset (1,000 videos, 802 unique creators, Sep–Dec 2020): **205 creators**
qualify as promising.

**This dataset is a historical sample, not live data.** The UI labels the actual date range on
screen so nobody mistakes it for current trending data — the point of this prototype is to prove
the methodology, not to claim these are today's trending creators.

## How the Q&A chat stays honest

See `docs/accuracy-honesty.md` for the plain-English version, and `docs/data-flow.md` for the
technical data flow. Short version: questions that can be answered by computing over the real
data (rankings, totals, comparisons) are answered by code, not guessed by the model — every such
answer is labeled **"Computed from data."** Questions that require judgment (would this creator
fit a brand?) are answered by the model's own reasoning and are labeled **"AI opinion"** so
nobody mistakes a guess for a fact.

## Running locally

### Backend (Python, `uv`)

```bash
cd backend
uv sync
cp .env.example .env   # then add your ANTHROPIC_API_KEY
uv run uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`. Run the test suite with `uv run pytest`.

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3000` (or the next free port). The frontend talks to the backend at
`http://localhost:8000` by default — override with `NEXT_PUBLIC_API_BASE_URL` if needed.

## Deployment

Two independent Vercel projects point at this same repo:

- **Frontend project** — Root Directory `frontend/`. Deploys on push, no configuration needed
  beyond Next.js's Vercel defaults.
- **Backend project** — Root Directory `backend/`. Deploys on push via the `api/index.py` +
  `vercel.json` entrypoint (a small, well-known pattern for running FastAPI on Vercel's Python
  runtime). Set `ANTHROPIC_API_KEY` and `FRONTEND_ORIGIN` (the deployed frontend's URL) as
  environment variables on this project.

No database, no auth — this prototype doesn't need either (see the requirements doc for why).
