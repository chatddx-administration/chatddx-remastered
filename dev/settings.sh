# shellcheck shell=bash
# Usage: . dev/settings.sh, then setting <array> <key>, from the repository's root: sets the array to the words
# settings.toml holds at the dotted key.
setting() {
  local -n words=$1
  local said
  said="$(python3 -c '
import sys, tomllib
with open("settings.toml", "rb") as f:
    held = tomllib.load(f)
for key in sys.argv[1].split("."):
    held = held[key]
print(*held)
' "$2")" || return
  # shellcheck disable=SC2034
  read -ra words <<<"$said"
}
