#!/usr/bin/env bash
# Usage: ./check.sh [stage]..., from the repository's root in the dev shell with its database
# up (dev-db start). Each stage checks one thing and writes nothing git tracks; the stages
# named, or all of them, run side by side, and it fails, saying which did, if any does.
# What a stage says is also logged to dev/logs/<stage>.log, as write.sh moves it to logs/.
set -euo pipefail

STAGES=(openapi stamps locale pending format types frontend docs tests browser)

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
  chatddx locale pending
}

format() {
  ruff format --check
  chatddx stamp reflow --check
}

types() {
  ruff check
  basedpyright
}

frontend() {
  pnpm --dir frontend check
  timed pnpm --dir frontend test
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

# Duplication: src/chatddx/test/costs.py:Cost reads these columns, in this order; it
# spools them likewise only in a checkout, as told by dev/costs.tsv being there.
spooled() {
  local took
  [[ -n ${MACHINE_CLASS:-} && -f dev/costs.tsv ]] || return 0
  took="$(awk -v a="$1" -v b="$EPOCHREALTIME" 'BEGIN { printf "%.1f", b - a }')"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$MACHINE_CLASS" "$took" \
    "$2" "${CHATDDX_BESIDE:-0}" "$(git rev-parse --short HEAD 2>/dev/null)" "$3" >>dev/costs-spool.tsv
}

logged() {
  local rc=$?
  [[ -z $began ]] || spooled "$began" "$rc" "./check.sh $stage"
  exec >&- 2>&-
  wait "${teed[@]}"
}

timed() {
  local began="$EPOCHREALTIME" rc=0
  "$@" || rc=$?
  spooled "$began" "$rc" "$*"
  return "$rc"
}

fail() {
  echo "$1" >&2
  exit 1
}

# Optimization: a stage that passes holds what it read as good in dev/<stage>-good, and is
# skipped till that changes: the tree a commit of the worktree would hold, and for docs
# also origin/main, which refcheck checks the commits the docs name against. Outside a git
# checkout, such as nix's, nothing is held.
# Duplication: the tree as dev/agent.sh's tree makes it, but for what checks write.
inputs() {
  local index
  index="$(mktemp)"
  if cp "$(git rev-parse --git-path index 2>/dev/null)" "$index" 2>/dev/null &&
    GIT_INDEX_FILE="$index" git add --all 2>/dev/null &&
    GIT_INDEX_FILE="$index" git rm -r --cached --quiet --ignore-unmatch dev/costs.tsv logs; then
    GIT_INDEX_FILE="$index" git write-tree
    [[ $1 != docs ]] || git rev-parse --verify --quiet origin/main || true
  fi
  rm -f "$index"
}

# Optimization: stages named together run side by side, and what each says is said in
# order once all have run.
# Accommodating for bash, which ignores errexit wherever a status is tested: each stage
# runs as a process of its own, so that it still stops at its first failure.
# Dependency: frontend's check and browser's build both write
# frontend/src/lib/api/schema.d.ts (pnpm types), so they run one after the other.
lane() {
  local stage rc
  trap exit INT TERM
  for stage in "$@"; do
    rc=0
    bash "${BASH_SOURCE[0]}" "$stage" >"$said/$stage.out" 2>"$said/$stage.err" || rc=$?
    echo "$rc" >"$said/$stage.rc"
  done
}

# Accommodating for a terminal, which interrupts only its foreground process group, and for
# bash, whose background commands ignore interrupts while job control is off: each lane
# runs as a job, a process group of its own without the terminal's input, and relay hands
# it what this gets, then waits for it to stop at the end of its stage.
relay() {
  kill -"$1" -- "${lanes[@]/#/-}" 2>/dev/null || true
  wait
  trap - "$1"
  kill -"$1" $$
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
  stage="${stages[0]}"
  good="dev/$stage-good"
  log="dev/logs/$stage.log"
  mkdir -p dev/logs
  printf '%s %s ./check.sh %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$(git rev-parse --short HEAD 2>/dev/null)" "$stage" >"$log"
  began=""
  teed=()
  exec > >(tee -a "$log")
  teed+=("$!")
  exec 2> >(tee -a "$log" >&2)
  teed+=("$!")
  trap logged EXIT
  was="$(inputs "$stage")"
  if [[ -n $was && $was == "$(cat "$good" 2>/dev/null)" ]]; then
    echo "• $stage: unchanged since it passed ($good)" >&2
    exit
  fi
  echo "• $stage" >&2
  began="$EPOCHREALTIME"
  "$stage"
  if [[ -n $was && $was == "$(inputs "$stage")" ]]; then
    echo "$was" >"$good"
  fi
  exit
fi
said="$(mktemp -d)"
trap 'rm -rf "$said"' EXIT
lanes=()
trap 'relay INT' INT
trap 'relay TERM' TERM
set -m
export CHATDDX_BESIDE=$((${#others[@]} - (${#built[@]} ? 0 : 1)))
if [[ ${#built[@]} -gt 0 ]]; then
  lane "${built[@]}" </dev/null &
  lanes+=("$!")
fi
for stage in "${others[@]}"; do
  lane "$stage" </dev/null &
  lanes+=("$!")
done
wait
failed=()
for stage in "${stages[@]}"; do
  cat "$said/$stage.err" >&2
  cat "$said/$stage.out"
  [[ $(cat "$said/$stage.rc") -eq 0 ]] || failed+=("$stage")
done
[[ ${#failed[@]} -eq 0 ]] || fail "• failed: ${failed[*]}"
