# Creator Signal Prototype — Requirements

## Context

The user's friend is Head of Creative Partnerships at a talent agency. Today she decides which creators/content are worth pursuing through a mix of gut feel from her network plus an analyst pulling raw-number spreadsheets — no structured process, and shrinking time for either as she gets busier. The goal is a working, deployable prototype that turns a batch of TikTok data into (1) a one-screen "at a glance" view of the most promising creators, and (2) a plain-English Q&A chat so she can follow up ("which creators get the most engagement?") without needing the analyst. Trust in the answer matters as much as the answer itself — she's non-technical and will act on this.

Source data: `2026datathon_interview_data.csv` — 1,000 TikTok video rows, 802 unique creators (some with multiple videos in-batch), columns `views, likes, comments, shares, author_verified, primary_hashtag, music_name, music_is_original, duration_sec, caption, upload_date, author_name, video_id`. Upload dates span **2020-09-22 to 2020-12-21** — a historical sample, not live data. No `follower_count` column exists, so nothing can be normalized against audience size.

## Decisions

1. **Use case for "promising"**: mix of *recruit unsigned creators to the roster* and *pitch existing creators to brand clients* — the definition should work for both, not optimize for one.

2. **Definition of "promising"** (data-grounded, tested against real rows before locking):
   - Aggregate per creator (`author_name`) across all their videos in the batch.
   - **Reach floor: total views ≥ 250,000** (221 of 802 creators survive — a curated pool sized for a one-screen summary).
   - **Reach ceiling: total views ≤ 10,000,000.** Excludes ~16 already-massive/celebrity-tier accounts (e.g. `billieeilish` at 250.8M views) — already famous, not realistic recruit/pitch targets. Ceiling values from 5M–20M all exclude essentially the same cluster, so 10M is a round-number default, not a contested threshold.
   - **Rank survivors by engagement rate** = average of `(likes + comments + shares) / views` per video, averaged across the creator's videos in-batch. Pure reach surfaces celebrities; pure engagement rate surfaces 1-video noise accounts. Floor + ceiling + rate avoids both failure modes.
   - Population reference: median creator in this batch sits at ~96K total views, ~8.7% engagement rate.

3. **Data vintage handling**: Treated as an **illustrative methodology demo**, not live signal. The UI must visibly label the actual date range (Sep–Dec 2020) and frame the tool as "here's how we'd score a batch," not implying these are today's trending creators. A fresh-data refresh is explicitly future work.

4. **Q&A grounding (the core trust mechanism)** — **Hybrid**:
   - Questions that map to a clear computation (rankings, totals, comparisons) go through a **code layer that computes over the real CSV rows** — the LLM translates the question into a structured computation, code executes it, LLM phrases the result in plain English. Numbers can never be invented.
   - Interpretive/judgment questions (e.g. "would this creator fit a beauty brand?") get an LLM-reasoned answer, but the response must be **visibly labeled as an AI opinion**, distinct from computed-fact answers.
   - This is the structural mechanism behind the "keep AI's answers accurate and honest" stretch goal.

5. **Data exposure / deployment**: Deploy to a **public, shareable link, no auth**. Creator handles and stats published as-is — this is public TikTok data already visible on-platform.

6. **Stretch goals — in scope**: README, a data-flow sketch (question → LLM → computation layer → CSV → answer), and a short non-technical accuracy/honesty note.

## Deliverables

- **Screen 1 — At a Glance Summary**: single screen, ranked list of promising creators (250K–10M pool, engagement-rate ranked). Per creator: handle, total views, engagement rate, verified badge, video count, one representative caption/hashtag. Header stat bar: creators evaluated (802), promising-cutoff count (221), dataset date range with "sample data" label.
- **Screen 2 — Q&A Chat**: natural-language input, hybrid-grounded answers, visible computed-fact vs. AI-interpretation labeling.
- **README.md**: what it does, how "promising" is defined and why, how to run/deploy.
- **Data flow sketch**: question → LLM parses intent → computation layer runs against CSV → (if judgment question) LLM reasons with labeled-opinion output → plain-English answer.
- **Accuracy/honesty note**: 3-5 plain-English lines, written for the non-technical reader, on why hybrid grounding keeps answers trustworthy.

## Non-Goals

- No live TikTok API integration or data refresh pipeline — batch CSV only.
- No user accounts, auth, or multi-user features.
- No brand-fit/content-category ML classification.
- No follower-count-normalized metrics — source data doesn't support it; documented limitation, not an engineering gap to close.

## Assumptions

- 10M view ceiling is a default, not a rigorously optimized cutoff.
- Summary screen shows the full 221-creator pool or a reasonable top-N slice (e.g. top 25-50) — exact display count is a UI-layer call for `/ce-plan`.
- Verified badge is displayed as metadata only, not used as a scoring input.

## Outstanding Questions

- Exact top-N cutoff for what's visible on the single summary screen without scrolling.
- Whether `/ce-plan` should recommend a specific frontend/backend stack now, or the user wants that decided live (per this template's `CLAUDE.md`, framework choice is meant to be a live product decision).

## Verification (Definition of Done)

- Summary screen shows the promising pool, correctly reflecting the floor/ceiling/rate rules — spot-check 3-5 creators against raw CSV math.
- Q&A chat answers "which creators get the most engagement?" with real, CSV-derived numbers matching the summary screen's ranking — no hallucinated names or stats.
- At least one judgment-style question returns a response visibly labeled as AI opinion, not fact.
- Deployed link is publicly reachable, both screens load, dataset date range is visible on-screen.
- README, data-flow sketch, and accuracy/honesty note exist and are readable by a non-technical person.

## Recommended Next Step

Hand off to `/ce-plan` to turn these locked product decisions into an implementation plan (stack choice, file layout, the computation-layer design for grounded Q&A, deployment target setup).

---
Full decision rationale and dialogue history: `docs/decisions.local.md` (local only, not checked into the repo).
