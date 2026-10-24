#!/usr/bin/env bash
# Usage: run by Claude Code as a cloud session starts or resumes (.claude/settings.json).
# Brings the session's branch to its latest commit, provisions what AGENTS.md's environment
# asks for on the container's own PostgreSQL 16, and hands .env-container and the venv to
# the session's commands.
set -euo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

cd "$CLAUDE_PROJECT_DIR"
exec 3>&1 1>&2

# Dependency: Claude Code's input to the hook, whose source says whether the session starts
# or resumes, and which a run after the fast-forward below is handed.
session_source="${SESSION_START_SOURCE-}"
[ -n "$session_source" ] || [ -t 0 ] || session_source="$(jq -r '.source // empty' 2>/dev/null || true)"

# Policy: a branch is fast-forwarded only, and only with nothing of its own in the way;
# otherwise it is left as it is and the session is told.
latest() {
  local branch upstream base
  branch="$(git symbolic-ref --quiet --short HEAD)" || {
    echo "session-start: HEAD is detached, so no branch was brought up to date" >&3
    return 0
  }
  for wait in 2 4 8 16 0; do
    git fetch --quiet origin && break
    if [ "$wait" = 0 ]; then
      echo "session-start: git fetch origin failed, so $branch may be behind origin" >&3
      return 0
    fi
    sleep "$wait"
  done
  upstream="origin/$branch"
  if ! git rev-parse --verify --quiet "$upstream" >/dev/null; then
    :
  elif git merge-base --is-ancestor "$upstream" HEAD; then
    :
  elif git merge-base --is-ancestor HEAD "$upstream" && [ -z "$(git status --porcelain)" ]; then
    git merge --ff-only --quiet "$upstream"
    echo "session-start: $branch fast-forwarded to $upstream, $(git log -1 --format='%h %s')" >&3
    # Heads-up: bash reads a script as it runs it, and the fast-forward may have changed this
    # one, so the rest is run by the new one.
    exec env SESSION_START_LATEST=1 SESSION_START_SOURCE="$session_source" "$0" >&3 3>&-
  else
    echo "session-start: $branch has diverged from $upstream or has changes of its own, so it was left as it is" >&3
  fi
  base="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD || echo origin/main)"
  if [ "$base" != "$upstream" ] && git rev-parse --verify --quiet "$base" >/dev/null &&
    ! git merge-base --is-ancestor "$base" HEAD; then
    echo "session-start: $base is $(git rev-list --count "HEAD..$base") commit(s) past $branch, at $(git log -1 --format='%h %s' "$base")" >&3
  fi
}

# Policy: docs are stamped against the commit the session starts at, or the latest a human
# made since; resumed in a container of its own, the session finds it again as the latest
# commit on its branch that isn't of its own git identity.
pinned() {
  local pin human
  pin="$(git rev-parse --git-path chatddx-stamp-base)"
  human="$(git log --first-parent --format='%H %ae' HEAD |
    awk -v me="$(git config user.email || true)" '$2 != me && !found { print $1; found = 1 }')"
  if [ "$session_source" = startup ]; then
    git rev-parse HEAD >"$pin"
  elif [ -n "$human" ] && { [ ! -s "$pin" ] || git merge-base --is-ancestor "$(cat "$pin")" "$human"; }; then
    echo "$human" >"$pin"
  fi
  stamp_base=""
  [ ! -s "$pin" ] || stamp_base="$(cat "$pin")"
}

[ -n "${SESSION_START_LATEST:-}" ] || latest
pinned

set -a
. ./.env-container
set +a

PGCONF=/etc/postgresql/16/main
osuser="$(id -un)"

venv() {
  uv sync --frozen
}

database() {
  [ -d "$PGCONF" ] || {
    echo "session-start: no PostgreSQL 16 cluster at $PGCONF" >&2
    exit 1
  }
  local changed=0
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
  elif [ "$changed" = 1 ]; then
    pg_ctlcluster 16 main reload
  fi
  # Heads-up: psycopg reads a SQL_ASCII database's text as bytes, which chatddx migrate
  # takes for none of its migrations applied.
  encoding="$(runuser -u postgres -- psql -tAc "SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = 'template1'")"
  [ "$encoding" = UTF8 ] || {
    echo "session-start: the cluster's template1 is $encoding, not UTF8, as dev-db's initdb makes it" >&2
    exit 1
  }
  if [ -z "$(runuser -u postgres -- psql -tAc "SELECT 1 FROM pg_roles WHERE rolname = 'chatddx'")" ]; then
    runuser -u postgres -- psql -q -v ON_ERROR_STOP=1 <src/chatddx/store/setup.sql
  fi
  .venv/bin/chatddx migrate
}

frontend() {
  pnpm --dir frontend install --frozen-lockfile
  pnpm --dir frontend build
}

handed() {
  [ -n "${CLAUDE_ENV_FILE:-}" ] || return 0
  cat >>"$CLAUDE_ENV_FILE" <<ENV
set -a
. "$CLAUDE_PROJECT_DIR/.env-container"
set +a
export VIRTUAL_ENV="$CLAUDE_PROJECT_DIR/.venv"
export PATH="$CLAUDE_PROJECT_DIR/.venv/bin:\$PATH"
ENV
  [ -z "$stamp_base" ] || echo "export CHATDDX_STAMP_BASE=$stamp_base" >>"$CLAUDE_ENV_FILE"
}

venv
database
frontend
handed
pinned_at="no commit: chatddx stamp docs needs CHATDDX_STAMP_BASE"
[ -z "$stamp_base" ] || pinned_at="$(git log -1 --format='%h %s' "$stamp_base")"
echo "session-start: at $(git log -1 --format='%h %s'); docs are stamped against $pinned_at; venv, database $DB_NAME (migrated) and frontend build ready; .env-container and .venv are in every command's environment" >&3
