#!/usr/bin/env bash
# Stop hook: full test suite(s) must pass before session ends.
# Exit 2 = blocking, feeds stderr back to Claude to keep working instead of stopping.
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
FAIL=0

if [ -f "$PROJECT_DIR/frontend/package.json" ] && jq -e '.scripts.test' "$PROJECT_DIR/frontend/package.json" >/dev/null 2>&1; then
  if ! OUT=$(cd "$PROJECT_DIR/frontend" && npm test --silent 2>&1); then
    echo "Frontend test suite is red. Fix before ending the session, or tell the user explicitly it's broken:" >&2
    echo "$OUT" >&2
    FAIL=1
  fi
fi

if [ -f "$PROJECT_DIR/backend/pyproject.toml" ] && [ -d "$PROJECT_DIR/backend/tests" ]; then
  if ! OUT=$(cd "$PROJECT_DIR/backend" && uv run pytest 2>&1); then
    echo "Backend test suite is red. Fix before ending the session, or tell the user explicitly it's broken:" >&2
    echo "$OUT" >&2
    FAIL=1
  fi
fi

[ "$FAIL" -eq 1 ] && exit 2
exit 0
