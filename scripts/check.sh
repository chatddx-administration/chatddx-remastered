#!/usr/bin/env bash
# Usage: scripts/check.sh [docs|package|frontend|browser]..., from the repository's root
# in the dev shell with its database up (dev-db start). Each stage checks what a kind of
# change can break and writes nothing git tracks; with no stage named, the stages of what
# git says changed.
set -euo pipefail

docs() {
  python scripts/refcheck.py
}

package() {
  chatddx openapi | cmp -s - frontend/openapi.json ||
    fail "frontend/openapi.json is behind the code: run chatddx openapi > frontend/openapi.json"
  chatddx stamp --check
  crosscheck
  ruff check
  basedpyright
  pytest -p chatddx.test.budget -m "not browser"
}

frontend() {
  pnpm --dir frontend check
  pnpm --dir frontend test
}

# Compromise: on their own, for the browser they start, with what they say they skip.
browser() {
  pnpm --dir frontend build
  pytest -m browser -rs
}

# Policy: the API's Python surface and its OpenAPI document change together, so one
# changing alone is worth a look, not a failure.
crosscheck() {
  git rev-parse --git-dir >/dev/null 2>&1 || return 0
  local openapi surface
  openapi="$(git status --porcelain -- frontend/openapi.json)"
  surface="$(git status --porcelain -- docs/surfaces/api.md)"
  if [[ -n $openapi && -z $surface ]] || [[ -z $openapi && -n $surface ]]; then
    echo "flag: one of frontend/openapi.json and docs/surfaces/api.md changed, the other didn't" >&2
  fi
}

fail() {
  echo "$1" >&2
  exit 1
}

# Accommodating for the docs referring to the code, which a change in the code can break.
changed() {
  local paths
  paths="$(git status --porcelain | cut -c4-)"
  grep -qE '^(docs/|agents/|AGENTS\.md|README\.md|scripts/refcheck\.py|src/)' <<<"$paths" && echo docs
  grep -qE '^(src/|worlds/|pyproject\.toml|uv\.lock|frontend/openapi\.json)' <<<"$paths" && echo package
  grep -qE '^(frontend/|worlds/(test|sample)/_data/schemas/)' <<<"$paths" && echo frontend
  grep -qE '^(frontend/|src/chatddx/portal/)' <<<"$paths" && echo browser
  return 0
}

stages=("$@")
if [[ ${#stages[@]} -eq 0 ]]; then
  mapfile -t stages < <(changed)
  [[ ${#stages[@]} -gt 0 ]] || echo "• nothing to check: no stage reads what git says changed" >&2
fi
for stage in "${stages[@]}"; do
  case "$stage" in
  docs | package | frontend | browser)
    echo "• $stage" >&2
    "$stage"
    ;;
  *) fail "no stage $stage: docs, package, frontend or browser" ;;
  esac
done
