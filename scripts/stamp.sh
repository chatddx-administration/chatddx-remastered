#!/usr/bin/env bash
# Usage: stamp.sh [message], in the dev shell, once the stamps pending are stamped. Checks the baseline the next session starts from, commits all
# that changed as the message, "stamp" unless given one, pushes, and prints the revision
# to start that session at.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

./check.sh baseline >&2
git add -A
git diff --cached --quiet || git commit --quiet -m "${1:-stamp}"
as.sh "$CHATDDX_DEV" git push --quiet -u origin HEAD
git rev-parse --short HEAD
