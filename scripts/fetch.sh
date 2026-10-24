#!/usr/bin/env bash
# Usage: fetch.sh, in the dev shell, on the branch an agent hands over on. Pulls what it
# pushed and checks the baseline, which flags the stamps pending for a human to stamp.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

as.sh "$CHATDDX_DEV" git pull --quiet --ff-only origin "$(git branch --show-current)"
./check.sh baseline
