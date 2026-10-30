# Whoopses and asserts in `portal`

Written by `chatddx-dev index` from the `raise Whoops` and `assert` statements in `[parts.portal]`'s code in `settings.toml`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/portal/pages.py:_refusal`

```
assert error.wording is not None
```

## `src/chatddx/portal/pages.py:paged.handle`

```
assert isinstance(said, Response)
```

```
assert isinstance(error.detail, str)
```

## `src/chatddx/portal/pages.py:to_sign_in`

```
assert isinstance(e, SignInFirst)
```

## `src/chatddx/portal/world.py:_pinned`

```
assert isinstance(engine, LocalEngine | RemoteEngine)
```

## `src/chatddx/portal/world.py:world`

```
assert isinstance(held, World)
```
