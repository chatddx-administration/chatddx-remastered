# Stamp

`chatddx stamp` writes, from the code of each package of `src/chatddx/settings.py:STAMPED`, its public surface in
`docs/surfaces/`, an index of its comments in `docs/comments/` and an index of its whoopses and asserts in
`docs/whoopses/`, its tests left out, keeping what changed since the last stamp as a git conflict for a human to stamp
(`src/chatddx/stamp/markers.py:stamped`). `chatddx stamp write` writes what is behind the code; `chatddx stamp check`
writes nothing, flags stamps pending and fails while a file is behind the code, and with `--baseline` on stamps pending
too. The code is read, never imported (`src/chatddx/stamp/code.py:Code`), and a function's raises and findings are
traced through its private helpers (`src/chatddx/stamp/trace.py:Trace`), a `Whoops` left out. How to read what it writes
is in docs/surfaces.md.
