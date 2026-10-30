#!/usr/bin/env bash
# Usage: [STAMPED=<commit>] ./dev/write.sh [write]..., from the repository's root in the dev
# shell. Writes the writes named, or all of them, one after the other in the order of WRITES,
# what follows from the code and the docs, and says what it wrote, stopping at the first that
# fails. Each but costs and logs writes what the check of its name checks; stamps writes the
# prose's against the commit dev/stamped.sh tells, or guesses.
set -euo pipefail
. dev/stamped.sh

WRITES=(costs logs format openapi locale index stamps)

costs() {
  chatddx-dev costs write
}

# Duplication: dev/agent.sh:moved_logs.
logs() {
  local moved
  shopt -s nullglob
  moved=(dev/state/logs/*.log)
  shopt -u nullglob
  ((${#moved[@]})) || return 0
  mkdir -p logs
  mv "${moved[@]}" logs/
  echo "logs: moved"
}

format() {
  ruff format --quiet
  chatddx-dev stamp reflow
  shfmt --write dev
  RUST_LOG=warn taplo fmt
}

openapi() {
  doc="$(mktemp)"
  trap 'rm -f "$doc"' EXIT
  chatddx openapi >"$doc"
  cat "$doc" >frontend/openapi.json
}

locale() {
  chatddx locale write
}

index() {
  chatddx-dev index
}

stamps() {
  local base
  base="$(stamped guessed)"
  chatddx-dev stamp docs "$base"
}

for write in "$@"; do
  [[ " ${WRITES[*]} " == *" $write "* ]] || {
    echo "no write $write: ${WRITES[*]}" >&2
    exit 1
  }
done
for write in "${WRITES[@]}"; do
  [[ $# -eq 0 || " $* " == *" $write "* ]] || continue
  "$write"
done
