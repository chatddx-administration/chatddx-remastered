#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PGCONF=/etc/postgresql/16/main
STARTED=dev/session-start
TURN=dev/turn-start
REFUSED=dev/refused
CHECKED_AT_SESSION_START=(openapi stamps locale pending fuzzy format types frontend docs)
CHECKED_AT_HAND_OVER=(format types frontend docs tests browser)
REFUSED_AT_TURN_START=(openapi locale)
TOLD_AT_TURN_START=(pending fuzzy format types frontend)

remote() {
  [[ ${CLAUDE_CODE_REMOTE:-} == true ]]
}

# Accommodating for Claude Code, which hands what session-start writes to $CLAUDE_ENV_FILE
# to the session's commands but not to its hooks.
if remote; then
  set -a
  . ./.env-container
  set +a
  export VIRTUAL_ENV="$PWD/.venv" PATH="$PWD/.venv/bin:$PATH"
fi

event=""
[[ -t 0 ]] || event="$(cat)"

field() {
  [[ -n $event ]] || return 0
  python3 -c 'import json, sys; v = json.load(sys.stdin).get(sys.argv[1], ""); print(v if isinstance(v, str) else json.dumps(v))' \
    "$1" <<<"$event" 2>/dev/null || true
}

session-start() {
  local state=()
  case "$(field source)" in
  resume | clear | compact) ;;
  *) state+=(fresh) ;;
  esac
  if remote && ! provisioned; then
    state+=(unprovisioned refused)
  elif [[ ${state[*]} == fresh ]] && ! session-checked; then
    state+=(refused)
  fi
  echo "${state[*]}" >"$STARTED"
}

session-checked() {
  checked "${CHECKED_AT_SESSION_START[@]}"
  ((${#failed[@]})) || return 0
  refuse "$(named "${failed[@]}")" details
  sections
  return 1
}

# Accommodating for bash, which ignores errexit wherever a status is tested: provisioning
# runs as a process of its own, so that it still stops at its first failure.
provisioned() {
  said="$(bash dev/agent.sh provision 2>&1)" && return
  refuse "a container that fails to provision" details
  echo "$said"
  return 1
}

provision() {
  uv sync --frozen
  database
  pnpm --dir frontend install --frozen-lockfile
  pnpm --dir frontend build
  [[ -z ${CLAUDE_ENV_FILE:-} ]] || cat >>"$CLAUDE_ENV_FILE" <<ENV
set -a
. "$PWD/.env-container"
set +a
export VIRTUAL_ENV="$PWD/.venv"
export PATH="$PWD/.venv/bin:\$PATH"
ENV
}

database() {
  local osuser changed=0 encoding
  osuser="$(id -un)"
  [[ -d $PGCONF ]] || {
    echo "no PostgreSQL 16 cluster at $PGCONF" >&2
    exit 1
  }
  if ! grep -qE "^chatddx\s+$osuser\s+chatddx_writer\s*$" "$PGCONF/pg_ident.conf"; then
    printf 'chatddx %s chatddx\nchatddx %s chatddx_writer\n' "$osuser" "$osuser" \
      >>"$PGCONF/pg_ident.conf"
    changed=1
  fi
  if grep -qE '^local\s+all\s+all\s+peer\s*$' "$PGCONF/pg_hba.conf"; then
    sed -i -E 's/^(local\s+all\s+all\s+peer)\s*$/\1 map=chatddx/' "$PGCONF/pg_hba.conf"
    changed=1
  fi
  if ! pg_ctlcluster 16 main status >/dev/null 2>&1; then
    pg_ctlcluster 16 main start
  elif [[ $changed == 1 ]]; then
    pg_ctlcluster 16 main reload
  fi
  # Heads-up: psycopg reads a SQL_ASCII database's text as bytes, which chatddx migrate
  # takes for none of its migrations applied.
  encoding="$(runuser -u postgres -- psql -tAc "SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = 'template1'")"
  [[ $encoding == UTF8 ]] || {
    echo "the cluster's template1 is $encoding, not UTF8, as dev-db's initdb makes it" >&2
    exit 1
  }
  if [[ -z "$(runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname = 'chatddx'")" ]]; then
    runuser -u postgres -- psql -q -v ON_ERROR_STOP=1 <src/chatddx/store/setup.sql
  fi
  chatddx migrate
}

turn-start() {
  local state=() refused="" was rev
  if [[ -f $STARTED ]]; then
    read -ra state <"$STARTED"
    rm -f "$STARTED"
  fi
  [[ " ${state[*]} " != *" refused "* ]] || refused=refused
  was="$(git rev-parse HEAD)"
  if ! remote || [[ " ${state[*]} " == *" unprovisioned "* ]]; then
    :
  elif [[ " ${state[*]} " == *" fresh "* ]] && rev="$(supplied)"; then
    if ! moved "$rev"; then
      refused=refused
    elif [[ $(git rev-parse HEAD) != "$was" ]]; then
      if provisioned && session-checked; then
        [[ -z $refused ]] ||
          echo "Work isn't refused after all: $rev, the commit the prompt starts at, passes what session-start refused work for."
        refused=""
      else
        refused=refused
      fi
    fi
  elif [[ -z $refused ]]; then
    synced
    if [[ $(git rev-parse HEAD) != "$was" ]]; then
      provisioned && turn-checked || refused=refused
    fi
  fi
  git rev-parse HEAD >"$TURN"
  if [[ -n $refused ]]; then
    : >"$REFUSED"
  else
    rm -f "$REFUSED"
  fi
}

supplied() {
  local prompt
  prompt="$(field prompt)"
  [[ $prompt =~ ^[[:space:]]*At[[:space:]]+([0-9a-f]{7,40})([^0-9A-Za-z]|$) ]] || return 1
  echo "${BASH_REMATCH[1]}"
}

moved() {
  local sha branch
  git fetch --quiet origin 2>/dev/null || true
  sha="$(git rev-parse --verify --quiet "$1^{commit}")" || {
    refuse "$1, the commit the prompt starts at, which isn't to be found"
    return 1
  }
  [[ $sha != "$(git rev-parse HEAD)" ]] || return 0
  if branch="$(git symbolic-ref --quiet --short HEAD)"; then
    git checkout --quiet -B "$branch" "$sha"
  else
    git checkout --quiet --detach "$sha"
  fi
}

# Policy: the branch follows what the operator pushes to it, by fast-forward only and only
# with nothing of its own in the way, or else by the agent's merge; a fetch that fails is
# tried again at the next turn's start.
synced() {
  local branch upstream
  branch="$(git symbolic-ref --quiet --short HEAD)" || return 0
  upstream="origin/$branch"
  git fetch --quiet origin 2>/dev/null || return 0
  if ! git rev-parse --verify --quiet "$upstream" >/dev/null || git merge-base --is-ancestor "$upstream" HEAD; then
    return 0
  fi
  if git merge-base --is-ancestor HEAD "$upstream" && [[ -z $(git status --porcelain) ]]; then
    git merge --ff-only --quiet "$upstream"
  else
    echo "$upstream has commits $branch lacks, up to $(git log -1 --format='%h %s' "$upstream"):" \
      "commit what changed and merge $upstream before going on."
  fi
}

turn-checked() {
  local refusing=() telling=() stage
  checked "${REFUSED_AT_TURN_START[@]}" "${TOLD_AT_TURN_START[@]}"
  ((${#failed[@]})) || return 0
  for stage in "${failed[@]}"; do
    if [[ " ${REFUSED_AT_TURN_START[*]} " == *" $stage "* ]]; then
      refusing+=("$stage")
    else
      telling+=("$stage")
    fi
  done
  ((${#refusing[@]} == 0)) || refuse "$(named "${refusing[@]}")" details
  ((${#telling[@]} == 0)) || echo "Tell the user about $(named "${telling[@]}"), with what follows, and go on."
  sections
  ((${#refusing[@]} == 0))
}

refuse() {
  echo "Work is refused, for $1: tell the user so${2:+, with what follows,} and commit no changes this turn."
}

checked() {
  local line
  failed=()
  said="$(./check.sh "$@" 2>&1)" && return
  line="$(grep '^• failed: ' <<<"$said" | tail -n 1)" || true
  if [[ -n $line ]]; then
    read -ra failed <<<"${line#• failed: }"
  else
    failed=("$@")
  fi
}

sections() {
  awk -v kept=" ${failed[*]} " '/^• / { name = $0; sub(/^• /, "", name); on = index(kept, " " name " ") > 0 } on' <<<"$said"
}

named() {
  local stage names=()
  for stage in "$@"; do
    case $stage in
    openapi) names+=("openapi out of sync") ;;
    stamps) names+=("stamps out of sync") ;;
    locale) names+=("locale out of sync") ;;
    pending) names+=("pending stamps") ;;
    fuzzy) names+=("fuzzy or untranslated messages") ;;
    format) names+=("formatting errors") ;;
    types) names+=("lint or type errors") ;;
    frontend) names+=("frontend type or test errors") ;;
    docs) names+=("broken references") ;;
    tests) names+=("failing tests") ;;
    browser) names+=("failing browser tests") ;;
    esac
  done
  printf '%s, ' "${names[@]}" | sed 's/, $//'
}

# Policy: turn-end has the turn go on to set right what it found, but only once a turn,
# lest the turn never end.
turn-end() {
  local start again="" before
  [[ $(field stop_hook_active) != true ]] || again=yes
  [[ ! -e $REFUSED ]] || return 0
  start="$(cat "$TURN" 2>/dev/null)" ||
    ended "turn-end has no commit the turn started at to stamp against: run ./dev/agent.sh turn-start first."
  [[ $(git rev-parse HEAD) != "$start" || -n $(git status --porcelain) ]] || return 0
  before="$(tree)"
  step ./write.sh "$start" ||
    ended "$stepped fails, as below: fix it before you end the turn, or tell the user why you can't." "$said"
  untranslated || [[ -n $again ]] ||
    ended "Translate the messages left untranslated, marking each fuzzy, before you end the turn:" "$said"
  if [[ $(tree) != "$before" ]]; then
    step git add --all && step git commit --quiet -m turn-end ||
      ended "$stepped fails, as below: see to it, and commit and push what turn-end wrote." "$said"
  fi
  step git push --quiet -u origin HEAD || ended "git push fails, as below: see to it, and push the branch." "$said"
}

ended() {
  [[ -z $again ]] || exit 0
  printf '%s\n' "$@" >&2
  exit 2
}

step() {
  stepped="$*"
  said="$("$@" 2>&1)"
}

untranslated() {
  ! step chatddx locale pending || return 0
  said="$(grep -E ': [1-9][0-9]* untranslated' <<<"$said")" || return 0
  return 1
}

tree() {
  local index
  index="$(mktemp)"
  cp "$(git rev-parse --git-path index)" "$index"
  GIT_INDEX_FILE="$index" git add --all
  GIT_INDEX_FILE="$index" git write-tree
  rm -f "$index"
}

hand-over() {
  local start again="fix it and run ./dev/agent.sh hand-over again." budget
  if [[ -e $REFUSED ]]; then
    echo "Work is refused this turn, so nothing is handed over: tell the user so."
    return
  elif ! start="$(cat "$TURN" 2>/dev/null)"; then
    echo "hand-over has no commit the turn started at to stamp against: run ./dev/agent.sh turn-start first."
    return
  fi
  if ! step ./write.sh "$start"; then
    printf '%s\n' "$stepped fails, as below: $again" "$said"
    return
  fi
  if ! untranslated; then
    printf '%s\n' "Translate the messages left untranslated, marking each fuzzy, then run ./dev/agent.sh hand-over again:" "$said"
    return
  fi
  if ! { step git add --all && { git diff --cached --quiet || step git commit --quiet -m hand-over; }; } ||
    ! step git push --quiet -u origin HEAD; then
    printf '%s\n' "$stepped fails, as below: see to it, and commit and push the branch." "$said"
    return
  fi
  checked "${CHECKED_AT_HAND_OVER[@]}"
  budget="$(grep -E '^(mark slow|unmark): ' <<<"$said")" || true
  if ((${#failed[@]})); then
    echo "Handed over with $(named "${failed[@]}"), as below: $again"
    sections
  fi
  [[ -z $budget ]] || printf '%s\n' "Flip what the budget suggests, should it feel right:" "$budget"
}

# Accommodating for Claude Code, which adds what a hook says to the session only if it
# exits 0, and what a Stop hook says only if it exits 2.
case "${1:-}" in
session-start | turn-start | turn-end | hand-over | provision)
  "$1"
  exit 0
  ;;
*)
  echo "usage: ./dev/agent.sh {session-start | turn-start | turn-end | hand-over}" >&2
  exit 1
  ;;
esac
