# Stamp

Stamp is a tool that forces a review by injecting git conflict markers between what's already signed and what's
suggested. The indexes are written so (`docs/parts/index.md`); docs in prose are stamped against the base commit with
`chatddx-dev stamp docs <base>`, the commit `dev/stamped.sh` tells.
