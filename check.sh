#!/usr/bin/env bash
# Usage: ./check.sh [stage]..., from the repository's root in the dev shell with its database
# up (dev-db start). Each stage checks one thing and writes nothing git tracks; the stages
# named, or all of them, run side by side, and it fails, saying which did, if any does.
set -euo pipefail

STAGES=(openapi stamps locale pending fuzzy format types frontend docs tests browser)

openapi() {
  chatddx openapi | cmp -s - frontend/openapi.json ||
    fail "frontend/openapi.json is behind the code: run chatddx openapi > frontend/openapi.json"
}

stamps() {
  chatddx stamp check
}

locale() {
  chatddx locale check
}

pending() {
  chatddx stamp pending
}

fuzzy() {
  chatddx locale pending
}

format() {
  ruff format --check
  prettier --check
}

# Policy: prettier leaves a doc that holds stamps pending as it is, as it would read their
# markers as markdown, till it is stamped.
prettier() {
  local held=()
  mapfile -t held < <(git grep --untracked -l -e '^>>>>>>> @''stamp$' -- '*.md' | sed 's/^/!/')
  frontend/node_modules/.bin/prettier "$@" . "${held[@]}"
}

types() {
  ruff check
  basedpyright
}

frontend() {
  pnpm --dir frontend check
  pnpm --dir frontend test
}

docs() {
  chatddx refcheck
}

tests() {
  pytest -n 4 -p chatddx.test.budget
}

# Compromise: on their own, for the browser they start.
browser() {
  pnpm --dir frontend build
  pytest -m browser
}

fail() {
  echo "$1" >&2
  exit 1
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
[[ ${#stages[@]} -gt 0 ]] || stages=("${STAGES[@]}")
built=()
others=()
for stage in "${stages[@]}"; do
  [[ " ${STAGES[*]} " == *" $stage "* ]] || fail "no stage $stage: ${STAGES[*]}"
  case "$stage" in
  frontend | browser) built+=("$stage") ;;
  *) others+=("$stage") ;;
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
