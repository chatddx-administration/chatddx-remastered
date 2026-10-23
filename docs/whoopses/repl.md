# Whoopses and asserts in `chatddx.repl`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/repl/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/repl/inspecting.py:_abridged`

```
assert isinstance(schema, dict)
```

## `src/chatddx/repl/inspecting.py:_by_judge`

```
assert graded.score is not None
```

## `src/chatddx/repl/inspecting.py:_of_case`

```
assert graded.score is not None
```

## `src/chatddx/repl/inspecting.py:_scored_with`

```
assert graded.score is not None
```

## `src/chatddx/repl/inspecting.py:_show_variation`

```
assert isinstance(messages, list)
```

```
assert isinstance(message, dict)
```

## `src/chatddx/repl/render.py:JudgeLines.event`

```
assert self.asked is not None
```

## `src/chatddx/repl/render.py:show_table`

```
assert g.score is not None
```

## `src/chatddx/repl/reviewing.py:_means`

```
assert graded.score is not None
```

## `src/chatddx/repl/running.py:_tagged`

```
assert skeleton is not None
```

## `src/chatddx/repl/running.py:run`

```
assert skeleton is not None
```
