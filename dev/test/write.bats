#!/usr/bin/env bats

setup() {
  cd "$BATS_TEST_TMPDIR"
  export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  export CALLS="$BATS_TEST_TMPDIR/calls"
  unset STAMPED MAIN
  mkdir bin
  for tool in chatddx chatddx-dev ruff shfmt taplo; do
    printf '#!%s\necho "%s $*" >>"$CALLS"\n' "$BASH" "$tool" >"bin/$tool"
  done
  chmod +x bin/*
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
  git init -q -b main repo
  cd repo
  mkdir -p dev frontend
  cp "$BATS_TEST_DIRNAME/../write.sh" "$BATS_TEST_DIRNAME/../stamped.sh" dev/
  git add -A
  git commit -q -m base
  git switch -q -c feat
}

@test "write writes all, in order, the prose against the commit stamped" {
  git update-ref refs/stamped/feat HEAD
  run ./dev/write.sh
  [ "$status" -eq 0 ]
  [ "$(cut -d' ' -f1,2 "$CALLS" | tr '\n' ,)" = "chatddx-dev costs,ruff format,chatddx-dev stamp,shfmt --write,taplo fmt,chatddx openapi,chatddx locale,chatddx-dev index,chatddx-dev stamp," ]
  [ "$(tail -n 1 "$CALLS")" = "chatddx-dev stamp docs $(git rev-parse HEAD)" ]
}

@test "write writes those named alone, in its own order" {
  STAMPED=given run ./dev/write.sh stamps openapi
  [ "$status" -eq 0 ]
  [ "$(cat "$CALLS")" = "$(printf '%s\n' "chatddx openapi" "chatddx-dev stamp docs given")" ]
}

@test "write refuses a write it doesn't have, and writes nothing" {
  run ./dev/write.sh openapi nope
  [ "$status" -eq 1 ]
  [ "$output" = "no write nope: costs logs format openapi locale index stamps" ]
  [ ! -e "$CALLS" ]
}

@test "write guesses the commit stamped as where HEAD left main" {
  echo work >work
  git add work
  git commit -q -m work
  run ./dev/write.sh stamps
  [ "$status" -eq 0 ]
  [ "$(tail -n 1 "$CALLS")" = "chatddx-dev stamp docs $(git rev-parse main)" ]
}

@test "write stops when there is no commit to stamp against" {
  git branch -q -m main trunk
  run ./dev/write.sh stamps
  [ "$status" -eq 1 ]
  [[ $output == "no commit to stamp against: "* ]]
  [ ! -e "$CALLS" ]
}
