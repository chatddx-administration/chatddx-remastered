# Whoopses and asserts in `chatddx.ledger`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/ledger/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/ledger/run.py:_rounds`

```
assert skeleton.max_rounds is not None
```

```
assert previous is not None
```
