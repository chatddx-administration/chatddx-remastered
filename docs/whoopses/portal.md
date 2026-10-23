# Whoopses and asserts in `chatddx.portal`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/portal/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

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
