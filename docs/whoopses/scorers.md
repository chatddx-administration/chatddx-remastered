# Whoopses and asserts in `chatddx.scorers`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/scorers/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/scorers/verdicts.py:_points`

```
assert isinstance(top, int | float)
```

## `src/chatddx/scorers/verdicts.py:_scored`

```
assert verdicts is not None
```
