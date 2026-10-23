# Whoopses and asserts in `chatddx.runner`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/runner/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/runner/rounds.py:converse`

```
assert previous.response is not None
```

## `src/chatddx/runner/score.py:Grading._judged`

```
assert view.judge is not None
```
