# feat: Creator Signal Prototype — Technical Plan

**Origin:** `docs/brainstorms/2026-08-17-creator-signal-prototype-requirements.md`

## Context

The requirements doc locked the product shape: a one-screen "promising creators" summary (250K–10M view creators ranked by engagement rate) plus a Q&A chat with hybrid-grounded answers (code computes stats, LLM labels opinions), deployed publicly with no auth, working off a static 2020 CSV framed as a methodology demo. This plan covers the HOW: stack, file layout, and the computation/LLM orchestration design.

Evaluated the `vintasoftware/nextjs-fastapi-template` GitHub repo as a candidate base (active, MIT, 325 stars). Its headline value — `fastapi-users` JWT auth, Postgres, Alembic migrations, an items-CRUD dashboard — is exactly what the requirements doc marks a non-goal (no auth, no DB, no user accounts). The one genuinely reusable piece is FastAPI-on-Vercel's serverless entrypoint shape (`api/index.py` re-exporting the FastAPI `app` + a `vercel.json` routing everything to it). **Decision: hand-roll a minimal Next.js + FastAPI pair, borrowing only that entrypoint pattern — do not clone the template.**

---

## Key Technical Decisions

1. **Split stack, no shared runtime.** `frontend/` — Next.js (App Router, TypeScript). `backend/` — FastAPI (Python, `uv`), matching this repo's own `CLAUDE.md` convention (hooks already wired for `npm`/frontend and `uv`/backend). No unified Next.js-API-routes approach — CSV/pandas computation and the Anthropic tool-use orchestration are more natural in Python than in a Node runtime, and the dual-subproject scaffold is already the template's convention.

2. **No database.** The CSV is loaded into memory via pandas once, at backend process start (module-level load in `backend/app/data.py`), and the promising-pool computation (floor/ceiling/rank) runs once and is cached in memory. Non-goal per requirements: no persistent storage, no user accounts.

3. **Deployment: two independent Vercel projects, native git-integration deploy.** Root Directory = `frontend/` for one project, `backend/` for the other, each pointed at this same GitHub repo. Vercel's default "deploy on push to main" is left **enabled** (unlike the evaluated template, which disables it because it needs a DB-migration step in its build command — we have no migration step, so the default suffices). No custom GitHub Actions needed. Backend gets the borrowed 4-line pattern:
   ```python
   # backend/api/index.py
   from app.main import app
   ```
   ```json
   // backend/vercel.json
   { "routes": [{ "src": "/(.*)", "dest": "api/index.py" }] }
   ```

4. **LLM: Anthropic Python SDK, `claude-sonnet-5`, Tool Runner.** User confirmed Sonnet 5 over Opus 5 (quality/cost balance for this task) and over Haiku 4.5 (judgment-question quality would suffer). Hybrid grounding (per origin doc decision 4) implemented via `client.beta.messages.tool_runner`:
   - Three `@beta_tool`-decorated functions — `rank_creators`, `get_creator_stats`, `compare_creators` — each backed by real pandas computation over the loaded CSV. The model calls these for stat/ranking questions; results are real numbers, never invented.
   - When no tool matches (interpretive questions — "would this creator fit a beauty brand?"), the model answers directly. The backend tags this response `"kind": "opinion"` vs `"kind": "computed"` in the API response so the frontend can visibly label it.
   - No thinking/effort tuning needed at this scale — defaults are fine; skip streaming for `/api/chat` initially (small payloads, simple chat UI) unless verification shows latency is an issue.

5. **CORS.** FastAPI backend allows the deployed frontend origin (env var `FRONTEND_ORIGIN`) plus `localhost` for dev.

---

## Output Structure

```
frontend/
  app/
    page.tsx                # Screen 1: at-a-glance summary
    chat/
      page.tsx               # Screen 2: Q&A chat
    layout.tsx
  lib/
    api.ts                    # fetch wrappers for backend endpoints
  package.json
  vercel.json
backend/
  api/
    index.py                  # Vercel entrypoint — re-exports app
  app/
    main.py                   # FastAPI app, CORS, route registration
    data.py                   # CSV load + promising-pool computation (pandas)
    tools.py                  # rank_creators / get_creator_stats / compare_creators
    llm.py                    # Anthropic client, tool_runner orchestration, opinion routing
    routes/
      summary.py               # GET /api/summary
      chat.py                  # POST /api/chat
  tests/
    test_data.py
    test_tools.py
    test_chat.py
  pyproject.toml
  vercel.json
  data/
    2026datathon_interview_data.csv
README.md                     # ships with repo: what it does, how "promising" is defined, how to run/deploy
docs/
  data-flow.md                # stretch: question -> LLM -> computation layer -> CSV -> answer sketch
  accuracy-honesty.md          # stretch: 3-5 plain-English lines on hybrid-grounding trust mechanism
```

---

### U1. Backend data layer — CSV load + promising-pool computation

**Goal:** Load the CSV once, compute the 250K–10M engagement-rate-ranked promising pool, expose it as an importable, testable module.

**Requirements:** Origin doc Decision 2 (definition), Decision 3 (vintage labeling).

**Dependencies:** none.

**Files:** `backend/app/data.py`, `backend/tests/test_data.py`, `backend/data/2026datathon_interview_data.csv` (copy from source), `backend/pyproject.toml` (add `pandas`).

**Approach:** Module-level function `load_dataset() -> pd.DataFrame` reads the CSV once at import time. `compute_promising_pool(df) -> list[dict]` aggregates per `author_name` (sum views, avg engagement rate per video, video count, verified flag), filters `250_000 <= total_views <= 10_000_000`, sorts by avg engagement rate descending. A `get_dataset_meta()` returns `{total_creators, promising_count, date_range: (min, max) of upload_date}` for the summary header.

**Patterns to follow:** None yet in repo — this is the first backend module. Keep pandas usage straightforward (groupby + agg), no premature optimization.

**Test scenarios:**
- Loading the CSV returns 1000 rows.
- `compute_promising_pool` returns exactly 205 creators (250K floor gives 221 candidates; 16 of those exceed the 10M ceiling and are excluded — combined floor+ceiling pool is 205, not the floor-only 221 figure that appeared earlier in dialogue).
- `billieeilish` is excluded (total views > 10M ceiling).
- A known top-rate creator (`reus.fx`, ~40% rate) appears near the top of the ranked pool.
- `get_dataset_meta()` returns date range `2020-09-22` to `2020-12-21`.

**Verification:** `pytest backend/tests/test_data.py` passes; spot-check 3 creators' computed views/rate against manual CSV math.

---

### U2. Backend summary endpoint

**Goal:** Serve the promising-creator pool and header stats to the frontend.

**Requirements:** Origin doc Deliverables — Screen 1.

**Dependencies:** U1.

**Files:** `backend/app/routes/summary.py`, `backend/app/main.py` (register route), `backend/tests/test_summary_route.py`.

**Approach:** `GET /api/summary` returns `{meta: {...}, creators: [...]}` where each creator has `handle, total_views, engagement_rate, verified, video_count, sample_caption`. No pagination needed at 205 rows — frontend slices to a top-N display if needed (deferred UI decision per origin doc Outstanding Questions).

**Test scenarios:**
- `GET /api/summary` returns 200 with `meta.promising_count == 205`.
- Response creators are sorted descending by `engagement_rate`.
- Response includes `meta.date_range`.

**Verification:** `curl localhost:8000/api/summary | jq` shows expected shape; pytest route test passes.

---

### U3. LLM tool functions (grounded computation layer)

**Goal:** Give the LLM real, callable functions for stat/ranking questions.

**Requirements:** Origin doc Decision 4 (hybrid grounding — computation half).

**Dependencies:** U1.

**Files:** `backend/app/tools.py`, `backend/tests/test_tools.py`.

**Approach:** Three `@beta_tool`-decorated functions per `python/claude-api/tool-use.md`:
- `rank_creators(sort_by: str, min_views: int | None, max_views: int | None, limit: int) -> str` — filters/sorts the promising pool (or full dataset if the question is about all 802 creators, not just the promising ones — decide scope from the question via the `min_views`/`max_views` args the model supplies).
- `get_creator_stats(handle: str) -> str` — single creator's aggregated numbers.
- `compare_creators(handles: list[str]) -> str` — side-by-side stats for 2+ named creators.

Each returns a plain-text/JSON-string summary (not raw DataFrame) so the model can phrase a natural-language answer from it.

**Patterns to follow:** `python/claude-api/tool-use.md` — Tool Runner section, `@beta_tool` decorator usage.

**Test scenarios:**
- `rank_creators(sort_by="engagement_rate", limit=5)` returns the same top-5 as U1's computed pool.
- `get_creator_stats("reus.fx")` returns correct total views and rate.
- `compare_creators(["reus.fx", "immaculatebae"])` returns both creators' stats.
- `get_creator_stats("nonexistent_handle")` returns a clear "not found" message rather than raising.

**Verification:** `pytest backend/tests/test_tools.py` passes.

---

### U4. Chat endpoint — hybrid grounding orchestration

**Goal:** Wire the LLM (Claude Sonnet 5) + tools into a `/api/chat` endpoint that labels computed-fact vs. AI-opinion responses.

**Requirements:** Origin doc Decision 4 (full hybrid mechanism), Deliverable — Screen 2.

**Dependencies:** U3.

**Files:** `backend/app/llm.py`, `backend/app/routes/chat.py`, `backend/tests/test_chat.py`, `backend/app/main.py` (CORS + route registration), `backend/.env.example` (`ANTHROPIC_API_KEY`, `FRONTEND_ORIGIN`).

**Approach:** `POST /api/chat` accepts `{question: str}`. Uses `client.beta.messages.tool_runner(model="claude-sonnet-5", tools=[rank_creators, get_creator_stats, compare_creators], messages=[...])`. After the runner completes: if any tool was called during the turn, tag response `kind: "computed"`; if the model answered with no tool calls (pure reasoning), tag `kind: "opinion"`. Return `{answer: str, kind: "computed" | "opinion"}`.

**Technical design (directional):**
```
POST /api/chat {question}
  -> tool_runner(model=sonnet-5, tools=[rank_creators, get_creator_stats, compare_creators])
  -> did any tool_use occur this turn?
       yes -> kind = "computed"
       no  -> kind = "opinion"
  -> { answer, kind }
```

**Execution note:** Test-first for the kind-tagging logic specifically — it's the trust-critical piece and easy to get backwards.

**Test scenarios:**
- "Which creators get the most engagement?" → calls `rank_creators`, response `kind == "computed"`, answer references real creator handles from U1's pool.
- "Would `reus.fx` fit a skincare brand?" → no tool call, response `kind == "opinion"`.
- Empty/malformed question → 400 with clear error, not a 500.
- Question naming a nonexistent creator → tool returns "not found", LLM surfaces that gracefully rather than hallucinating stats.
- `ANTHROPIC_API_KEY` unset → clear startup or request-time error, not a silent failure.

**Verification:** `pytest backend/tests/test_chat.py` passes; manual `curl -X POST localhost:8000/api/chat -d '{"question":"..."}'` for both question types confirms correct `kind` tagging.

---

### U5. Frontend summary screen

**Goal:** Render the one-screen "at a glance" view.

**Requirements:** Origin doc Deliverable — Screen 1.

**Dependencies:** U2.

**Files:** `frontend/app/page.tsx`, `frontend/lib/api.ts`, `frontend/package.json`.

**Approach:** Server component fetches `/api/summary` at render time (or client-side fetch — implementer's call based on Vercel deploy latency in practice). Header stat bar: total creators evaluated, promising-cutoff count, dataset date range with a visible "sample data" label. Ranked list below: handle, total views, engagement rate, verified badge, video count, sample caption. Top-N display slice (exact N is the one open UI decision from the origin doc — default to top 50, adjustable).

**Patterns to follow:** None yet — first frontend page. Keep it plain (no heavy component library needed for a single list view); Tailwind is fine if scaffolded in, otherwise plain CSS.

**Test scenarios:**
- Page renders without error when `/api/summary` returns valid data.
- Date range and "sample data" label are visible on-screen (this is a hard requirement from the origin doc, not cosmetic).
- Test expectation: no automated test for visual layout — manual browser verification per the Definition of Done in the origin doc.

**Verification:** Load the page in a browser; confirm header stats and ranked list match `/api/summary`'s JSON; confirm date-range label is visible.

---

### U6. Frontend Q&A chat screen

**Goal:** Render the natural-language chat with computed-fact vs. AI-opinion labeling.

**Requirements:** Origin doc Deliverable — Screen 2.

**Dependencies:** U4.

**Files:** `frontend/app/chat/page.tsx`, `frontend/lib/api.ts` (extend).

**Approach:** Simple chat UI — text input, submit, message list. Each assistant message renders with a visible badge/label reflecting its `kind` (`computed` vs `opinion`) from the `/api/chat` response.

**Test scenarios:**
- Submitting a stat question ("which creators get the most engagement?") displays an answer labeled as computed/fact.
- Submitting a judgment question displays an answer labeled as AI opinion.
- Test expectation: no automated test for chat UI rendering — manual browser verification (send both question types, confirm labels differ) per the Definition of Done.

**Verification:** In-browser: ask both question types, confirm the label visibly differs and the computed answer's numbers match the summary screen's ranking.

---

### U7. Deploy config and stretch deliverables

**Goal:** Ship the public deploy setup plus the README, data-flow sketch, and accuracy/honesty note.

**Requirements:** Origin doc Decision 5 (deploy), Decision 6 (stretch goals — all in scope).

**Dependencies:** U1–U6 complete enough to deploy.

**Files:** `frontend/vercel.json` (if needed beyond defaults), `backend/vercel.json`, `backend/api/index.py`, `README.md`, `docs/data-flow.md`, `docs/accuracy-honesty.md`.

**Approach:** Two Vercel projects per Key Technical Decision 3. README covers: what the prototype does, the "promising" definition and why (floor/ceiling/rate rationale), how to run locally, how it's deployed. `docs/data-flow.md`: simple diagram/prose — question → LLM parses intent → tool call runs against CSV (or direct answer for judgment questions) → plain-English response. `docs/accuracy-honesty.md`: 3-5 plain-English lines for the non-technical reader (the friend) explaining that stat answers are computed by code, not guessed, and opinion answers are clearly labeled.

**Test expectation:** none — documentation and deploy config, not behavioral.

**Verification:** Both Vercel projects deploy successfully from a git push; deployed frontend can reach deployed backend (`/api/summary` and `/api/chat` both work end-to-end from the public URL); README/docs are readable by a non-technical person (the actual test from the origin doc: could the friend explain the methodology to someone else after reading them).

---

## Verification (End-to-End)

Matches the origin requirements doc's Definition of Done:
- Summary screen shows the promising pool correctly reflecting floor/ceiling/rate rules (spot-check 3-5 creators against raw CSV math).
- Chat answers "which creators get the most engagement?" with real, CSV-derived numbers matching the summary screen's ranking — no hallucinated names or stats.
- At least one judgment-style question returns a response visibly labeled as AI opinion.
- Deployed link is publicly reachable, both screens load, dataset date range is visible on-screen.
- README, data-flow sketch, and accuracy/honesty note exist and are readable by a non-technical person.

## Outstanding (deferred to implementation)

- Exact top-N cutoff for the summary screen display (default top 50, tune during U5).
- Whether `/api/chat` should stream responses — start without streaming, revisit if latency is an issue during verification.
