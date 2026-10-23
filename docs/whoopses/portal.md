# Whoopses and asserts in `chatddx.portal`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/portal/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/portal/pages.py:paged.handle`

```
assert isinstance(said, Response)
```

## `src/chatddx/portal/pages.py:to_sign_in`

```
assert isinstance(e, SignInFirst)
```

## `src/chatddx/portal/world.py:world`

```
assert isinstance(held, World)
```
