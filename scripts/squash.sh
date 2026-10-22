#!/usr/bin/env bash
# squash-to-main.sh <branch>
#
# If <branch> is <main> + 1..N commits, squash those commits into a single
# commit on <main> (git opens your editor for the message), then rebase
# <branch> onto <main> so the two are identical.
#
# Abort with an empty message or :cq in vim -> nothing is changed, exit 1.
# MAIN env var overrides the target branch (default: main).
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

# Branch must sit directly on top of main's tip.
git merge-base --is-ancestor "$main_sha" "$branch_sha" ||
  die "'$branch' is not based on the tip of '$main' (rebase it onto $main first)"

count=$(git rev-list --count "$main_sha..$branch_sha")
((count >= 1)) || die "'$branch' has no commits beyond '$main'"

# Clean working tree (untracked files are fine).
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "uncommitted changes; commit or stash first"
fi
[[ ! -d "$(git rev-parse --git-path rebase-merge)" && ! -d "$(git rev-parse --git-path rebase-apply)" ]] ||
  die "a rebase is in progress"

# Neither branch may be checked out in *another* worktree.
here=$(git rev-parse --show-toplevel)
while read -r wt ref; do
  [[ $wt == "$here" ]] && continue
  [[ $ref == "refs/heads/$main" || $ref == "refs/heads/$branch" ]] &&
    die "'${ref#refs/heads/}' is checked out in worktree $wt"
done < <(git worktree list --porcelain | awk '/^worktree /{w=substr($0,10)} /^branch /{print w, $2}')

# Remember where we were.
orig=$(git symbolic-ref -q --short HEAD || git rev-parse HEAD)

# Prefill the message with the branch's commit messages (oldest first).
msgfile=$(mktemp)
trap 'rm -f "$msgfile"' EXIT
git log --reverse --format='%B' "$main_sha..$branch_sha" >"$msgfile"

# Build the squash: HEAD = main, index/worktree = branch tip.
git checkout -q --detach "$branch_sha"
git reset -q --soft "$main_sha"

if ! git commit -e -F "$msgfile"; then
  # Empty message, :cq, or failing hook -> undo and bail.
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

# Fast-forward main (fails if main moved meanwhile).
git update-ref -m "squash-to-main: $branch" "refs/heads/$main" "$new" "$main_sha"

# Rebase branch onto main: nothing to replay, so branch == main afterwards.
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
