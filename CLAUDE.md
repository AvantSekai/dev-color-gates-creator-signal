# Product Template — CLAUDE.md

This repo is a **template**. Clone it per product (`~/sandbox/products/<name>`), wipe `.git`, `git init` fresh. Do not work directly in the template — improvements to the loop flow back here, product code never does.

Two subprojects: `frontend/` (TypeScript/npm) and `backend/` (Python/uv). Neither ships pre-baked framework or source layout — the first scaffold commit (FastAPI vs Django vs plain script, framework choice, etc.) is a product decision made live via `/ce-brainstorm`, not assumed up front. Until `frontend/package.json` / `backend/pyproject.toml` exist, the hooks below silently no-op for that subproject.

## Definition of done

A change is done when, in order:

1. **Typecheck clean** — no type errors in changed files (enforced live by the PostToolUse hook, not just at the end).
2. **Format clean** — formatter has run on every changed file.
3. **Tests pass** — full suite green (enforced by the Stop hook; a red suite blocks session end).
4. **Verified** — the behavior was actually exercised (browser, CLI run, API call, screenshot), not just typechecked. See `/verify`.
5. **Reviewed** — `/ce-code-review` run on the diff, findings addressed or explicitly deferred.
6. **Compounded** — `/ce-compound` run so the lesson/pattern from this change is captured for next time, not relearned.
7. **Committed** — with a message that states why, not what.

## Loop order

```
/ce-plan → /ce-work → /verify → /ce-code-review → /ce-compound → commit
```

Do not skip steps. Do not commit before the Stop hook has run clean once in the session.

## STRATEGY.md

Every product clone must fill in root `STRATEGY.md` (revenue target, users, target problem) before Phase 2 build work starts. It is empty of specifics on purpose — product details are captured live via `/ce-brainstorm` when a new product is founded from this template, not pre-baked into the template.

## Hooks (already wired, don't remove)

Single root config (`.claude/settings.json`) dispatches by which subproject the edited file lives in:

- **PostToolUse** on `Edit`/`Write`: `frontend/**/*.{ts,tsx,js,jsx}` → `prettier` + typecheck (npm). `backend/**/*.py` → `ruff format` + `mypy` if configured in `pyproject.toml`. Blocks on type errors, not on format/lint. See `.claude/hooks/post-edit-check.sh`.
- **Stop**: runs `npm test` in `frontend/` if it has a test script, and `uv run pytest` in `backend/` if a `tests/` dir exists. Either red suite blocks session end — fix it or explicitly tell the user it's broken before stopping.

## Plugins enabled for this repo

`compound-engineering`, `vercel`, `frontend-design` — all enabled in root `.claude/settings.json`, one config for both subprojects (no more per-stack on/off toggling now that config is merged).
