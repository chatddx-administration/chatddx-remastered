# Whoopses and asserts in `chatddx.runner`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/runner/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/runner/rounds.py:converse`

```
assert previous.response is not None
```

## `src/chatddx/runner/score.py:Grading._judged`

```
assert view.judge is not None
```
