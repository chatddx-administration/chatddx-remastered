# Whoopses and asserts in `chatddx.api`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/api/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/api/app.py:_http`

```
assert isinstance(e, HTTPException)
```

## `src/chatddx/api/app.py:_invalid`

```
assert isinstance(e, RequestValidationError)
```

## `src/chatddx/api/app.py:_lifespan.lifespan`

```
assert isinstance(held, AppState)
```

## `src/chatddx/api/app.py:_whoops`

```
assert isinstance(e, Whoops)
```

## `src/chatddx/api/state.py:state`

```
assert isinstance(held, AppState)
```
