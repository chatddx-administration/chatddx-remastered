#!/usr/bin/env bash
set -euo pipefail

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"
cd "$(git rev-parse --show-toplevel)"

REFUSED_AT_STAMP=(openapi locale pending)
TOLD_AT_FETCH=(pending)

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

fetch() {
  local branch=${1:-$(git branch --show-current)}
  as.sh "$CHATDDX_DEV" git fetch --quiet origin
  git switch --quiet "$branch"
  git merge --ff-only --quiet "origin/$branch"
  ./check.sh "${TOLD_AT_FETCH[@]}" || true
}

stamp() {
  ./check.sh "${REFUSED_AT_STAMP[@]}" >&2 || die "nothing was committed"
  git add -A
  git diff --cached --quiet || git commit --quiet -m "${1:-stamp}"
  [[ $(git rev-parse HEAD) == "$(git rev-parse --verify -q '@{u}')" ]] ||
    as.sh "$CHATDDX_DEV" git push --quiet -u origin HEAD
  git rev-parse --short HEAD
}

merge() {
  local main branch main_sha branch_sha count here wt ref orig msgfile new
  main=${MAIN:-main}
  branch=${1:-$(git branch --show-current)}

  [[ -n ${CHATDDX_DEV:-} ]] || die "CHATDDX_DEV is unset, so as.sh has no one to push as"
  command -v as.sh >/dev/null || die "no as.sh on PATH to push with"
  [[ $branch != "$main" ]] || die "branch must differ from $main"
  [[ ! -d "$(git rev-parse --git-path rebase-merge)" && ! -d "$(git rev-parse --git-path rebase-apply)" ]] ||
    die "a rebase is in progress"

  if [[ -n $(git status --porcelain) ]]; then
    [[ $(git branch --show-current) == "$branch" ]] || die "uncommitted changes; commit or stash first"
    git add -A
    git commit --quiet -m merge
  fi

  main_sha=$(git rev-parse --verify -q "refs/heads/$main^{commit}") || die "no local branch '$main'"
  branch_sha=$(git rev-parse --verify -q "refs/heads/$branch^{commit}") || die "no local branch '$branch'"

  git merge-base --is-ancestor "$main_sha" "$branch_sha" ||
    die "'$branch' is not based on the tip of '$main' (rebase it onto $main first)"

  count=$(git rev-list --count "$main_sha..$branch_sha")
  ((count >= 1)) || die "'$branch' has no commits beyond '$main'"

  here=$(git rev-parse --show-toplevel)
  while read -r wt ref; do
    [[ $wt == "$here" ]] && continue
    [[ $ref == "refs/heads/$main" || $ref == "refs/heads/$branch" ]] &&
      die "'${ref#refs/heads/}' is checked out in worktree $wt"
  done < <(git worktree list --porcelain | awk '/^worktree /{w=substr($0,10)} /^branch /{print w, $2}')

  orig=$(git symbolic-ref -q --short HEAD || git rev-parse HEAD)
  git checkout -q "$branch"
  ./check.sh pending >&2 || {
    git checkout -q "$orig"
    die "'$branch' has what is flagged above pending; nothing was merged"
  }

  msgfile=$(mktemp)
  trap "rm -f -- '$msgfile'" EXIT
  git log --reverse --format='%B' "$main_sha..$branch_sha" >"$msgfile"

  git checkout -q --detach "$branch_sha"
  git reset -q --soft "$main_sha"

  if ! git commit -e -F "$msgfile" >&2; then
    git reset -q --soft "$branch_sha"
    git checkout -q "$orig"
    die "commit aborted; nothing was changed"
  fi

  new=$(git rev-parse HEAD)
  [[ $(git rev-parse "$new^{tree}") == $(git rev-parse "$branch_sha^{tree}") ]] ||
    {
      git reset -q --soft "$branch_sha"
      git checkout -q "$orig"
      die "squash tree differs from '$branch' (hook modified files?); aborted"
    }

  git update-ref -m "squash-to-main: $branch" "refs/heads/$main" "$new" "$main_sha"
  git checkout -q "$main"
  as.sh "$CHATDDX_DEV" git push --quiet origin "$main"
  git branch -q -D "$branch"
  if git rev-parse --verify -q "refs/remotes/origin/$branch" >/dev/null; then
    as.sh "$CHATDDX_DEV" git push --quiet origin --delete "$branch"
  fi
  git rev-parse --short "$main"
}

case "${1:-}" in
fetch | stamp | merge) "$@" ;;
*) die "usage: ./dev/operator.sh {fetch [branch] | stamp [message] | merge [branch]}" ;;
esac
