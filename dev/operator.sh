#!/usr/bin/env bash
set -euo pipefail

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"
cd "$(git rev-parse --show-toplevel)"

MAIN=${MAIN:-main}
# shellcheck source=dev/settings.sh
. "$(dirname "${BASH_SOURCE[0]}")/settings.sh"
setting REFUSED_AT_STAMP operator.refused_at_stamp
setting TOLD_AT_FETCH operator.told_at_fetch

unmerged() {
  die "stamped but didn't merge: $*"
}

fetch() {
  local branch=${1:-$(git branch --show-current)}
  as.sh "$CHATDDX_DEV" git fetch -q --prune origin '+refs/heads/*:refs/remotes/origin/*' '+refs/stamped/*:refs/stamped/*'
  git switch -q "$branch"
  git merge --ff-only -q "origin/$branch"
  ./dev/check.sh "${TOLD_AT_FETCH[@]}" || true
}

# Policy: refs/stamped/<branch> marks what was stamped, for dev/stamped.sh to stamp against.
stamp() {
  local branch was
  branch=$(git branch --show-current)
  [[ -n ${CHATDDX_DEV:-} ]] || die "CHATDDX_DEV is unset, so as.sh has no one to push as"
  command -v as.sh >/dev/null || die "no as.sh on PATH to push with"
  [[ ! -d "$(git rev-parse --git-path rebase-merge)" && ! -d "$(git rev-parse --git-path rebase-apply)" ]] ||
    die "a rebase is in progress"
  [[ -n $branch ]] || die "HEAD is detached; switch to a branch"
  [[ $branch != "$MAIN" ]] || die "on $MAIN; switch to a branch"

  ./dev/check.sh "${REFUSED_AT_STAMP[@]}" >&2 || die "nothing was committed"
  git add -A
  git diff --cached --quiet || git commit -q -m "${1:-stamp}"
  was=$(git rev-parse --verify -q "refs/stamped/$branch") || true
  git update-ref "refs/stamped/$branch" HEAD
  [[ $(git rev-parse HEAD) == "$(git rev-parse --verify -q '@{u}')" && $was == "$(git rev-parse HEAD)" ]] ||
    as.sh "$CHATDDX_DEV" git push -q -u origin HEAD "+refs/stamped/$branch"
  git rev-parse --short HEAD
}

merge() {
  local branch main_sha branch_sha here wt ref msgfile new gone=()
  branch=${1:-$(git branch --show-current)}

  here=$(git rev-parse --show-toplevel)
  while read -r wt ref; do
    [[ $wt == "$here" ]] && continue
    [[ $ref == "refs/heads/$MAIN" || $ref == "refs/heads/$branch" ]] &&
      die "'${ref#refs/heads/}' is checked out in worktree $wt"
  done < <(git worktree list --porcelain | awk '/^worktree /{w=substr($0,10)} /^branch /{print w, $2}')
  main_sha=$(git rev-parse --verify -q "refs/heads/$MAIN^{commit}") || die "no local branch '$MAIN'"
  git merge-base --is-ancestor "$main_sha" "refs/heads/$branch" ||
    die "'$branch' is not based on the tip of '$MAIN' (rebase it onto $MAIN first)"

  if [[ $(git branch --show-current) != "$branch" ]]; then
    [[ -z $(git status --porcelain) ]] || die "uncommitted changes; commit or stash first"
    git switch -q "$branch"
  fi
  stamp >/dev/null

  branch_sha=$(git rev-parse HEAD)
  [[ $main_sha != "$branch_sha" ]] || unmerged "'$branch' has no commits beyond '$MAIN'"

  msgfile=$(mktemp)
  # shellcheck disable=SC2064
  trap "rm -f -- '$msgfile'" EXIT
  git log --reverse --format='%B' "$main_sha..$branch_sha" >"$msgfile"

  git checkout -q --detach "$branch_sha"
  git reset -q --soft "$main_sha"

  if ! git commit -q -e -F "$msgfile" >&2; then
    git reset -q --soft "$branch_sha"
    git checkout -q "$branch"
    unmerged "commit aborted"
  fi

  new=$(git rev-parse HEAD)
  [[ $(git rev-parse "$new^{tree}") == $(git rev-parse "$branch_sha^{tree}") ]] ||
    {
      git reset -q --soft "$branch_sha"
      git checkout -q "$branch"
      unmerged "squash tree differs from '$branch' (hook modified files?)"
    }

  git update-ref -m "squash-to-main: $branch" "refs/heads/$MAIN" "$new" "$main_sha"
  git checkout -q "$MAIN"
  as.sh "$CHATDDX_DEV" git push -q origin "$MAIN"
  git branch -q -D "$branch"
  git update-ref -d "refs/stamped/$branch"
  gone=("refs/stamped/$branch")
  if git rev-parse --verify -q "refs/remotes/origin/$branch" >/dev/null; then
    gone+=("$branch")
  fi
  as.sh "$CHATDDX_DEV" git push -q origin --delete "${gone[@]}"
  git rev-parse --short "$MAIN"
}

case "${1:-}" in
fetch | stamp | merge) "$@" ;;
*) die "usage: ./dev/operator.sh {fetch [branch] | stamp [message] | merge [branch]}" ;;
esac
