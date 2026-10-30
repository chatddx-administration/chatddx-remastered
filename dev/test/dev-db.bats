#!/usr/bin/env bats

setup() {
  DEVDB="$BATS_TEST_DIRNAME/../dev-db.sh"
  cd "$BATS_TEST_TMPDIR"
  export CHATDDX_STATE_HOME="$BATS_TEST_TMPDIR/state" REPO_ROOT="$BATS_TEST_TMPDIR/repo"
  export CALLS="$BATS_TEST_TMPDIR/calls"
  : >"$CALLS"
  PGDATA="$CHATDDX_STATE_HOME/dev-db/pgdata"
  PGSOCK="$CHATDDX_STATE_HOME/dev-db/pgsock"

  mkdir bin
  stub initdb 'mkdir -p "$2"'
  stub pg_ctl '
    data=$2
    case " $* " in
    *" status "*) [ -e "$data/running" ] ;;
    *" start "*)
      echo "a line the server logged" >"$data/server.log"
      [ -z "${PG_START_FAILS:-}" ] && touch "$data/running"
      ;;
    *" stop "*) rm "$data/running" ;;
    esac'
  stub psql 'echo "PGHOST=${PGHOST:-} PGUSER=${PGUSER:-} PGDATABASE=${PGDATABASE:-}" >>"$CALLS"; exit "${PSQL_EXIT:-0}"'
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

stub() {
  printf '#!%s\necho "%s $*" >>"$CALLS"\n%s\n' "$BASH" "$1" "$2" >"bin/$1"
  chmod +x "bin/$1"
}

called() { grep -c "^$1 " "$CALLS" || true; }

@test "start initializes, starts and sets up the database" {
  run bash "$DEVDB" start
  [ "$status" -eq 0 ]
  [ "$(called initdb)" -eq 1 ]
  [ -e "$PGDATA/running" ]
  [ -e "$PGDATA/.setup-done" ]
  [ -d "$PGSOCK" ]
  grep -q "^chatddx    $(id -un)          chatddx_writer$" "$PGDATA/pg_ident.conf"
  [ "$(cat "$PGDATA/pg_hba.conf")" = "local all all peer map=chatddx" ]
  grep -q -- "-f $REPO_ROOT/src/chatddx/store/setup.sql" "$CALLS"
}

@test "start again neither initializes nor sets up again" {
  bash "$DEVDB" start
  bash "$DEVDB" stop
  : >"$CALLS"
  run bash "$DEVDB" start
  [ "$status" -eq 0 ]
  [ "$(called initdb)" -eq 0 ]
  [ "$(called psql)" -eq 0 ]
  [ -e "$PGDATA/running" ]
}

@test "start says when postgres is already running" {
  bash "$DEVDB" start
  run bash "$DEVDB" start
  [ "$status" -eq 0 ]
  [ "$output" = "postgres is already running" ]
}

@test "start tells what the server logged when postgres fails to start" {
  PG_START_FAILS=1 run bash "$DEVDB" start
  [ "$status" -eq 1 ]
  [[ $output == *"postgres failed to start; last log lines:"* ]]
  [[ $output == *"a line the server logged"* ]]
  [ ! -e "$PGDATA/.setup-done" ]
}

@test "start tells how to reset when setup fails, and sets up again next time" {
  PSQL_EXIT=1 run bash "$DEVDB" start
  [ "$status" -eq 1 ]
  [[ $output == *"setup failed; reset with: dev-db stop && rm -rf $PGDATA"* ]]
  [ ! -e "$PGDATA/.setup-done" ]
  run bash "$DEVDB" start
  [ "$status" -eq 0 ]
  [ -e "$PGDATA/.setup-done" ]
}

@test "stop stops postgres, and says when it isn't running" {
  bash "$DEVDB" start
  run bash "$DEVDB" stop
  [ "$status" -eq 0 ]
  [ ! -e "$PGDATA/running" ]
  run bash "$DEVDB" stop
  [ "$output" = "postgres not running" ]
}

@test "status says whether postgres is running" {
  run bash "$DEVDB" status
  [ "$output" = stopped ]
  bash "$DEVDB" start
  run bash "$DEVDB" status
  [ "$output" = running ]
}

@test "reset stops postgres and removes its data and socket" {
  bash "$DEVDB" start
  run bash "$DEVDB" reset
  [ "$status" -eq 0 ]
  [ ! -e "$PGDATA" ]
  [ ! -e "$PGSOCK" ]
}

@test "enter runs psql as chatddx on the socket with the arguments given" {
  run bash "$DEVDB" enter -c "select 1"
  [ "$status" -eq 0 ]
  grep -q "^psql -c select 1$" "$CALLS"
  grep -q "^PGHOST=$PGSOCK PGUSER=chatddx PGDATABASE=chatddx$" "$CALLS"
}

@test "dev-db says how to use it" {
  run bash "$DEVDB"
  [ "$status" -eq 1 ]
  [[ $output == "Usage: dev-db "* ]]
}
