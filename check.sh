#!/usr/bin/env bash
# Usage: ./check.sh [docs|package|frontend|locale|format|browser|baseline]..., from the repository's root
# in the dev shell with its database up (dev-db start). Each stage checks what a kind of
# change can break and writes nothing git tracks; with no stage named, the stages of what
# changed since the branch left origin/main, or $CHECK_BASE. It fails if any stage does.
set -euo pipefail

docs() {
  chatddx refcheck
}

package() {
  chatddx openapi | cmp -s - frontend/openapi.json ||
    fail "frontend/openapi.json is behind the code: run chatddx openapi > frontend/openapi.json"
  chatddx stamp check
  crosscheck
  ruff check
  basedpyright
  pytest -n 4 -p chatddx.test.budget
}

frontend() {
  pnpm --dir frontend check
  pnpm --dir frontend test
}

locale() {
  chatddx locale check
}

format() {
  ruff format --check
  frontend/node_modules/.bin/prettier --check .
}

# Compromise: on their own, for the browser they start.
browser() {
  pnpm --dir frontend build
  pytest -m browser
}

# Policy: on a fresh commit before work starts, what it flags is for a human to settle
# before work proceeds, so it flags all of it at once and no change git sees runs it.
baseline() {
  local flagged=0
  chatddx refcheck | sed 's/^/flag: /' >&2 || flagged=1
  chatddx openapi | cmp -s - frontend/openapi.json || {
    echo "flag: frontend/openapi.json: behind the code at the baseline: the code changed without" \
      "chatddx openapi; investigate before work proceeds" >&2
    flagged=1
  }
  chatddx stamp check --baseline || flagged=1
  chatddx locale check --baseline || flagged=1
  return "$flagged"
}

# Policy: the API's Python surface and its OpenAPI document change together, so one
# changing alone is worth a look, not a failure.
crosscheck() {
  git rev-parse --git-dir >/dev/null 2>&1 || return 0
  local openapi surface
  openapi="$(git diff --name-only "$(base)" -- frontend/openapi.json)"
  surface="$(git diff --name-only "$(base)" -- docs/surfaces/api.md)"
  if [[ -n $openapi && -z $surface ]] || [[ -z $openapi && -n $surface ]]; then
    echo "flag: one of frontend/openapi.json and docs/surfaces/api.md changed, the other didn't" >&2
  fi
}

fail() {
  echo "$1" >&2
  exit 1
}

# Accommodating for commits between units of work, which squashing makes the branch's own.
base() {
  git merge-base HEAD "${CHECK_BASE:-origin/main}" 2>/dev/null || git rev-parse HEAD
}

# Accommodating for the docs referring to the code, which a change in the code can break.
changed() {
  local paths
  paths="$(git diff --name-only "$(base)" && git ls-files --others --exclude-standard)"
  grep -qE '^(docs/|agents/|AGENTS\.md|README\.md|src/)' <<<"$paths" && echo docs
  grep -qE '^(src/|worlds/|pyproject\.toml|uv\.lock|frontend/openapi\.json)' <<<"$paths" && echo package
  grep -qE '^(frontend/|worlds/(test|sample)/_data/schemas/)' <<<"$paths" && echo frontend
  grep -qE '^(src/chatddx/|frontend/src/)' <<<"$paths" && echo locale
  grep -qE '^(src/|frontend/|docs/|agents/|AGENTS\.md|README\.md|pyproject\.toml|\.prettier)' <<<"$paths" && echo format
  grep -qE '^(frontend/|src/chatddx/portal/)' <<<"$paths" && echo browser
  return 0
}

# Optimization: stages named together run side by side, and what each says is said in
# order once all have run.
# Accommodating for bash, which ignores errexit wherever a status is tested: each stage
# runs as a process of its own, so that it still stops at its first failure.
# Dependency: frontend's check and browser's build both write
# frontend/src/lib/api/schema.d.ts (pnpm types), so they run one after the other.
lane() {
  local stage rc
  for stage in "$@"; do
    rc=0
    bash "${BASH_SOURCE[0]}" "$stage" >"$said/$stage.out" 2>"$said/$stage.err" || rc=$?
    echo "$rc" >"$said/$stage.rc"
  done
}

stages=("$@")
if [[ ${#stages[@]} -eq 0 ]]; then
  mapfile -t stages < <(changed)
  [[ ${#stages[@]} -gt 0 ]] || echo "• nothing to check: no stage reads what the branch changed" >&2
fi
built=()
others=()
for stage in "${stages[@]}"; do
  case "$stage" in
  frontend | browser) built+=("$stage") ;;
  docs | package | locale | format | baseline) others+=("$stage") ;;
  *) fail "no stage $stage: docs, package, frontend, locale, format, browser or baseline" ;;
  esac
done
if [[ ${#stages[@]} -eq 1 ]]; then
  echo "• ${stages[0]}" >&2
  "${stages[0]}"
  exit
fi
said="$(mktemp -d)"
trap 'rm -rf "$said"' EXIT
[[ ${#built[@]} -eq 0 ]] || lane "${built[@]}" &
for stage in "${others[@]}"; do
  lane "$stage" &
done
wait
failed=()
for stage in "${stages[@]}"; do
  cat "$said/$stage.err" >&2
  cat "$said/$stage.out"
  [[ $(cat "$said/$stage.rc") -eq 0 ]] || failed+=("$stage")
done
[[ ${#failed[@]} -eq 0 ]] || fail "• failed: ${failed[*]}"
