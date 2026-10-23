# Whoopses and asserts in `chatddx.bench`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/bench/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/bench/runs.py:queue`

```
assert started.endpoint is not None
```

## `src/chatddx/bench/runs.py:start`

```
assert each.skeleton is not None
```

## `src/chatddx/bench/seen.py:Seen.handle`

```
raise Whoops(
    "No model in the Library holds these weights, though one should: "
    + "use another model meanwhile.",
    pass_on=f"{short(weights)} is held by no model thread: check the "
    + "RuntimeErrors",
)
```
