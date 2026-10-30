#!/usr/bin/env bats

setup() {
  OPERATOR="$BATS_TEST_DIRNAME/../operator.sh"
  cd "$BATS_TEST_TMPDIR"
  export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_EDITOR=true
  export CHATDDX_DEV=dev CHECKED="$BATS_TEST_TMPDIR/checked"
  unset MAIN

  mkdir bin
  printf '#!/bin/sh\nshift\nexec "$@"\n' >bin/as.sh
  chmod +x bin/as.sh
  export PATH="$BATS_TEST_TMPDIR/bin:$PATH"

  git init -q --bare -b main origin.git
  git clone -q origin.git repo 2>/dev/null
  cd repo
  printf '#!/bin/sh\necho "$@" >>"$CHECKED"\nexit "${CHECK_EXIT:-0}"\n' >check.sh
  chmod +x check.sh
  git add check.sh
  git commit -q -m init
  git push -q origin main
  git switch -q -c feat
  echo a >a
  git add a
  git commit -q -m work
}

subject() { git log -1 --format=%s "${1:-HEAD}"; }

committed() {
  echo "$1" >"$1"
  git add "$1"
  git commit -q -m "$1"
}

@test "stamp commits what is uncommitted as stamp, pushes it and prints its revision" {
  echo b >b
  run "$OPERATOR" stamp
  [ "$status" -eq 0 ]
  [ "$(subject)" = stamp ]
  [ "$output" = "$(git rev-parse --short HEAD)" ]
  [ "$(git rev-parse origin/feat)" = "$(git rev-parse HEAD)" ]
  [ -z "$(git status --porcelain)" ]
  [ "$(cat "$CHECKED")" = "openapi locale pending" ]
}

@test "stamp commits with the message given" {
  echo b >b
  run "$OPERATOR" stamp "a message"
  [ "$status" -eq 0 ]
  [ "$(subject)" = "a message" ]
}

@test "stamp pushes without a commit when nothing changed" {
  run "$OPERATOR" stamp
  [ "$status" -eq 0 ]
  [ "$(subject)" = work ]
  [ "$(git rev-parse origin/feat)" = "$(git rev-parse HEAD)" ]
}

@test "stamp commits nothing when a check fails" {
  echo b >b
  CHECK_EXIT=1 run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"nothing was committed"* ]]
  [ "$(subject)" = work ]
  [ -n "$(git status --porcelain)" ]
}

@test "stamp refuses on main" {
  git switch -q main
  echo b >b
  run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"on main"* ]]
  [ ! -e "$CHECKED" ]
}

@test "stamp refuses on a detached HEAD" {
  git switch -q --detach
  run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"detached"* ]]
}

@test "stamp stamps a branch not based on the tip of main" {
  git switch -q main
  committed ahead
  git switch -q feat
  echo b >b
  run "$OPERATOR" stamp
  [ "$status" -eq 0 ]
  [ "$(subject)" = stamp ]
}

@test "stamp refuses while a rebase is in progress" {
  mkdir "$(git rev-parse --git-path rebase-merge)"
  run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"a rebase is in progress"* ]]
}

@test "stamp refuses without CHATDDX_DEV" {
  unset CHATDDX_DEV
  run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"CHATDDX_DEV is unset"* ]]
}

@test "stamp takes MAIN for main" {
  git switch -q main
  git branch -q -m main trunk
  MAIN=trunk run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"on trunk"* ]]
}

@test "merge stamps, squashes the branch onto main, pushes it and deletes the branch" {
  echo b >b
  git push -q -u origin feat
  run "$OPERATOR" merge
  [ "$status" -eq 0 ]
  [ "$output" = "$(git rev-parse --short main)" ]
  [ "$(git branch --show-current)" = main ]
  [ "$(git rev-list --count main)" -eq 2 ]
  [ "$(git log -1 --format=%B main | grep -c .)" -eq 2 ]
  [ -e b ]
  [ "$(git rev-parse origin/main)" = "$(git rev-parse main)" ]
  [ -z "$(git ls-remote origin feat)" ]
  ! git rev-parse --verify -q refs/heads/feat
}

@test "merge switches to the branch named" {
  git switch -q main
  run "$OPERATOR" merge feat
  [ "$status" -eq 0 ]
  [ "$(subject main)" = work ]
}

@test "merge refuses to leave uncommitted changes for the branch named" {
  git switch -q main
  echo b >b
  run "$OPERATOR" merge feat
  [ "$status" -eq 1 ]
  [[ $output == *"uncommitted changes"* ]]
  [ "$(git branch --show-current)" = main ]
}

@test "merge says it stamped when the squash commit is aborted" {
  echo b >b
  GIT_EDITOR=false run "$OPERATOR" merge
  [ "$status" -eq 1 ]
  [[ $output == *"stamped but didn't merge: commit aborted"* ]]
  [ "$(git branch --show-current)" = feat ]
  [ "$(subject)" = stamp ]
  [ "$(subject main)" = init ]
  [ -z "$(git status --porcelain)" ]
}

@test "merge says it stamped when the branch has nothing beyond main" {
  git reset -q --hard main
  run "$OPERATOR" merge
  [ "$status" -eq 1 ]
  [[ $output == *"stamped but didn't merge: 'feat' has no commits beyond 'main'"* ]]
}

@test "merge merges nothing when stamp refuses" {
  echo b >b
  CHECK_EXIT=1 run "$OPERATOR" merge
  [ "$status" -eq 1 ]
  [[ $output == *"nothing was committed"* ]]
  [ "$(subject main)" = init ]
}

@test "merge refuses a branch not based on the tip of main, and stamps nothing" {
  git switch -q main
  committed ahead
  git switch -q feat
  echo b >b
  run "$OPERATOR" merge
  [ "$status" -eq 1 ]
  [[ $output == *"'feat' is not based on the tip of 'main'"* ]]
  [ ! -e "$CHECKED" ]
  [ "$(subject)" = work ]
}

@test "merge refuses a branch checked out in another worktree" {
  git switch -q main
  git worktree add -q ../other feat
  run "$OPERATOR" merge feat
  [ "$status" -eq 1 ]
  [[ $output == *"'feat' is checked out in worktree"* ]]
}

@test "operator refuses outside a git repository" {
  cd "$BATS_TEST_TMPDIR"
  run "$OPERATOR" stamp
  [ "$status" -eq 1 ]
  [[ $output == *"not inside a git repository"* ]]
}

@test "operator says how to use it" {
  run "$OPERATOR"
  [ "$status" -eq 1 ]
  [[ $output == *"usage:"* ]]
}
