#!/usr/bin/env bats

setup() {
  cd "$BATS_TEST_TMPDIR"
  export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
  unset STAMPED MAIN
  # shellcheck source=dev/stamped.sh
  . "$BATS_TEST_DIRNAME/../stamped.sh"
  git init -q -b main repo
  cd repo
  committed base
  git switch -q -c feat
}

committed() {
  echo "$1" >"$1"
  git add "$1"
  git commit -q -m "$1"
}

@test "stamped tells STAMPED as it is set" {
  STAMPED=given run stamped guessed
  [ "$status" -eq 0 ]
  [ "$output" = given ]
}

@test "stamped tells what refs/stamped holds for the branch while HEAD is on it" {
  committed stamp
  git update-ref refs/stamped/feat HEAD
  stamp=$(git rev-parse HEAD)
  committed work
  run stamped
  [ "$status" -eq 0 ]
  [ "$output" = "$stamp" ]
}

@test "stamped tells nothing but guessed when HEAD isn't on what refs/stamped holds" {
  committed stamp
  git update-ref refs/stamped/feat HEAD
  git switch -q main
  committed ahead
  git switch -q feat
  git rebase -q main
  run stamped
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  run stamped guessed
  [ "$status" -eq 0 ]
  [ "$output" = "$(git rev-parse main)" ]
}

@test "stamped guesses where HEAD left main without refs/stamped" {
  base=$(git rev-parse HEAD)
  git switch -q main
  committed ahead
  git switch -q feat
  committed work
  run stamped guessed
  [ "$status" -eq 0 ]
  [ "$output" = "$base" ]
}

@test "stamped fails, saying why, with nothing to guess" {
  git branch -q -m main trunk
  run stamped guessed
  [ "$status" -eq 1 ]
  [ "$output" = "no commit to stamp against: no refs/stamped/feat HEAD is on, nor a main HEAD shares history with" ]
}

@test "stamped tells nothing outside a git checkout" {
  cd "$BATS_TEST_TMPDIR"
  mkdir elsewhere
  cd elsewhere
  GIT_CEILING_DIRECTORIES="$BATS_TEST_TMPDIR" run stamped guessed
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
