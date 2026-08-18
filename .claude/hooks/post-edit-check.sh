#!/usr/bin/env bash
# PostToolUse hook (Edit|Write): format + typecheck the file that was just touched.
# Dispatches to frontend (npm/prettier/typecheck) or backend (uv/ruff/mypy) by path.
# Exit 2 = blocking error, fed back to Claude via stderr so it self-corrects.
set -euo pipefail

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

[ -z "$FILE" ] && exit 0

case "$FILE" in
  */frontend/*) SUBDIR="$PROJECT_DIR/frontend" ;;
  */backend/*) SUBDIR="$PROJECT_DIR/backend" ;;
  *) exit 0 ;;
esac

cd "$SUBDIR" || exit 0
FAIL=0

case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx)
    [ -f package.json ] || exit 0
    if jq -e '.scripts.format' package.json >/dev/null 2>&1; then
      npx --no-install prettier --write "$FILE" >/dev/null 2>&1 || true
    fi
    if jq -e '.scripts.typecheck' package.json >/dev/null 2>&1; then
      if ! OUT=$(npm run --silent typecheck 2>&1); then
        echo "Typecheck failed after editing $FILE:" >&2
        echo "$OUT" >&2
        FAIL=1
      fi
    fi
    ;;
  *.py)
    [ -f pyproject.toml ] || exit 0
    if grep -q '^\[tool\.ruff' pyproject.toml 2>/dev/null; then
      uv run ruff format "$FILE" >/dev/null 2>&1 || true
    fi
    if grep -q '^\[tool\.mypy\]' pyproject.toml 2>/dev/null; then
      if ! OUT=$(uv run mypy "$FILE" 2>&1); then
        echo "Typecheck failed after editing $FILE:" >&2
        echo "$OUT" >&2
        FAIL=1
      fi
    fi
    ;;
  *) exit 0 ;;
esac

[ "$FAIL" -eq 1 ] && exit 2
exit 0
