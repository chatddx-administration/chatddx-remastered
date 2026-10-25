# Whoopses and asserts in `chatddx.bench`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/bench/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

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
    "The model has no handle and can't be used.",
    pass_on=f"{display_digest(weights)} is held by no model thread: check the "
    + "RuntimeErrors",
)
```
