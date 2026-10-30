# Whoopses and asserts in `scripted`

Written by `chatddx-dev index` from the `raise Whoops` and `assert` statements in `[parts.scripted]`'s code in `settings.toml`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/scripted/run.py:ran_before`

```
assert skeleton is not None
```
