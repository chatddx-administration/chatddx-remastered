# Whoopses and asserts in `chatddx.catalog`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/catalog/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/catalog/model.py:About.of`

```
assert e.value is not None
```

```
assert e.person is not None
```

## `src/chatddx/catalog/read.py:tags_given`

```
assert entry.value is not None
```

## `src/chatddx/catalog/threads.py:_shape`

```
assert r is not None
```
