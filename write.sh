#!/usr/bin/env bash
# Usage: ./write.sh [commit], from the repository's root in the dev shell. Writes what
# follows from the code and the docs: the format, the OpenAPI document, the catalogs, and
# the surfaces and indexes, with what changed in them as stamps pending; given a commit,
# also each change to a doc in prose since it as stamps pending. It says what it wrote,
# and stops at the first that fails.
set -euo pipefail

ruff format --quiet
chatddx stamp reflow
doc="$(mktemp)"
trap 'rm -f "$doc"' EXIT
chatddx openapi >"$doc"
cat "$doc" >frontend/openapi.json
chatddx locale write
chatddx stamp write
[[ -z ${1:-} ]] || chatddx stamp docs "$1"
