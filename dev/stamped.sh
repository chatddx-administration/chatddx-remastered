# shellcheck shell=bash
# Usage: . dev/stamped.sh, from the repository's root, then stamped [guessed]: prints the commit stamps are made
# against: $STAMPED, or else what refs/stamped/<branch> holds, as ./dev/operator.sh stamp sets it, while HEAD is on it.
# Given guessed, it falls back to where HEAD left main, and fails, saying why, if there is none either. Outside a git
# checkout it prints nothing.
# Policy: the guess errs on stamping again: main is stamped, as ./dev/operator.sh merge squashes onto it, and where HEAD
# left it comes before anything stamped on the branch, so that what was stamped since is stamped again, not left out.
stamped() {
  local branch ref main
  if [[ -n ${STAMPED:-} ]]; then
    echo "$STAMPED"
    return
  fi
  git rev-parse --git-dir >/dev/null 2>&1 || return 0
  if branch="$(git symbolic-ref --quiet --short HEAD)" &&
    ref="$(git rev-parse --verify --quiet "refs/stamped/$branch^{commit}")" &&
    git merge-base --is-ancestor "$ref" HEAD; then
    echo "$ref"
    return
  fi
  [[ -n ${1:-} ]] || return 0
  for main in "origin/${MAIN:-main}" "${MAIN:-main}"; do
    git merge-base HEAD "$main" 2>/dev/null && return
  done
  echo "no commit to stamp against: no refs/stamped/${branch:-<branch>} HEAD is on, nor a main HEAD shares history with" >&2
  return 1
}
