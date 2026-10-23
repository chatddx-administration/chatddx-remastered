#!/usr/bin/env bash
# Usage: scripts/squash.sh [branch], the current one unless named, and MAIN for another
# target than main. Squashes the branch's commits beyond main's tip into one on main, with
# the message git opens an editor for, then rebases the branch onto main so the two are
# the same; an empty message, or :cq in vim, changes nothing.
set -euo pipefail

main=${MAIN:-main}
branch=${1:-$(git branch --show-current)}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"
[[ $branch != "$main" ]] || die "branch must differ from $main"

main_sha=$(git rev-parse --verify -q "refs/heads/$main^{commit}") || die "no local branch '$main'"
branch_sha=$(git rev-parse --verify -q "refs/heads/$branch^{commit}") || die "no local branch '$branch'"

git merge-base --is-ancestor "$main_sha" "$branch_sha" ||
  die "'$branch' is not based on the tip of '$main' (rebase it onto $main first)"

count=$(git rev-list --count "$main_sha..$branch_sha")
((count >= 1)) || die "'$branch' has no commits beyond '$main'"

if ! git diff --quiet || ! git diff --cached --quiet; then
  die "uncommitted changes; commit or stash first"
fi
[[ ! -d "$(git rev-parse --git-path rebase-merge)" && ! -d "$(git rev-parse --git-path rebase-apply)" ]] ||
  die "a rebase is in progress"

here=$(git rev-parse --show-toplevel)
while read -r wt ref; do
  [[ $wt == "$here" ]] && continue
  [[ $ref == "refs/heads/$main" || $ref == "refs/heads/$branch" ]] &&
    die "'${ref#refs/heads/}' is checked out in worktree $wt"
done < <(git worktree list --porcelain | awk '/^worktree /{w=substr($0,10)} /^branch /{print w, $2}')

orig=$(git symbolic-ref -q --short HEAD || git rev-parse HEAD)

msgfile=$(mktemp)
trap 'rm -f "$msgfile"' EXIT
git log --reverse --format='%B' "$main_sha..$branch_sha" >"$msgfile"

git checkout -q --detach "$branch_sha"
git reset -q --soft "$main_sha"

if ! git commit -e -F "$msgfile"; then
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

git checkout -q "$branch"
git rebase -q --onto "$main" "$branch"

[[ $(git rev-parse "$branch") == $(git rev-parse "$main") ]] || die "unexpected: '$branch' != '$main' after rebase"

[[ $orig != "$branch" ]] && git checkout -q "$orig"

cat <<EOF
Squashed $count commit(s) of '$branch' into $(git rev-parse --short "$new") on '$main'.
'$branch' now equals '$main'.

Old tip of '$branch': $branch_sha

Push:
  git push origin $main && git push --force-with-lease origin $branch

Followers with work on top of the old '$branch':
  git fetch && git rebase --onto origin/$branch $branch_sha <their-branch>
EOF
