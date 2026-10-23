# Whoopses and asserts in `chatddx.factors`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/factors/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/factors/base.py:Component.kind_name`

```
assert isinstance(kind, str)
```

## `src/chatddx/factors/scoring.py:fill_text`

```
assert op == "text@1"
```

## `src/chatddx/factors/select.py:_Parser.filter`

```
assert isinstance(step, Name | Index)
```

## `src/chatddx/factors/select.py:split`

```
assert op == "lines@1"
```
