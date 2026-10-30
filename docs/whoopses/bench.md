# Whoopses and asserts in `bench`

Written by `chatddx-dev index` from the `raise Whoops` and `assert` statements in `[parts.bench]`'s code in `settings.toml`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

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

## `src/chatddx/bench/updating.py:_kept`

```
assert proposed.digest is not None and proposed.proposal is not None
```

## `src/chatddx/bench/updating.py:_remodelled`

```
assert isinstance(was, str) and isinstance(now, str)
```
