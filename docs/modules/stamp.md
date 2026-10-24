# Stamp

```
AGENT: amend
What `chatddx stamp docs` writes, and what `chatddx stamp check` refuses of a doc.
---
`chatddx stamp` writes, from the code of each module of `src/chatddx/settings.py:STAGES`, its public surface in
`docs/surfaces/`, an index of its comments in `docs/comments/` and an index of its whoopses and asserts in
`docs/whoopses/`, each from the stage `src/chatddx/settings.py:STAMPED_FROM` says on, its tests left out, keeping what
changed since the last stamp as a git conflict for a human to stamp (`src/chatddx/stamp/markers.py:stamped`). `chatddx
stamp docs` keeps what changed in every other doc (`src/chatddx/stamp/__init__.py:documents`) since the commit
`src/chatddx/settings.py:stamp_base` names the same way, the doc whole and as written now
(`src/chatddx/stamp/markers.py:restamped`), and follows a doc's move as far as git sees it. `chatddx stamp write` writes
what is behind the code; `chatddx stamp check` writes nothing, flags stamps pending and fails while a file is behind the
code, a doc holds a conflict that isn't a stamp, a module in `src/chatddx/` has no stage or no module writes a file at
its stage, and with `--baseline` on stamps pending too. The code is read, never imported
(`src/chatddx/stamp/code.py:Code`), and a function's raises and findings are traced through its private helpers
(`src/chatddx/stamp/trace.py:Trace`), a `Whoops` left out. Each file it writes says how to read it before its first
entry.
```

`chatddx stamp` writes, from the code of each module of `src/chatddx/settings.py:STAGES`, its public surface in
`docs/surfaces/`, an index of its comments in `docs/comments/` and an index of its whoopses and asserts in
`docs/whoopses/`, each from the stage `src/chatddx/settings.py:STAMPED_FROM` says on, its tests left out, keeping what
changed since the last stamp as a git conflict for a human to stamp (`src/chatddx/stamp/markers.py:stamped`).
`chatddx stamp write` writes what is behind the code; `chatddx stamp check` writes nothing, flags stamps pending and
fails while a file is behind the code, a module in `src/chatddx/` has no stage or no module writes a file at its stage,
and with `--baseline` on stamps pending too. The code is read, never imported (`src/chatddx/stamp/code.py:Code`), and a
function's raises and findings are traced through its private helpers (`src/chatddx/stamp/trace.py:Trace`), a `Whoops`
left out. Each file it writes says how to read it before its first entry.
