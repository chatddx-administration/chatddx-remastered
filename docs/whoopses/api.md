# Whoopses and asserts in `chatddx.api`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/api/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

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

## `src/chatddx/api/state.py:state`

```
assert isinstance(held, AppState)
```
