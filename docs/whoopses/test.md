# Whoopses and asserts in `test`

Written by `chatddx-dev index` from the `raise Whoops` and `assert` statements in `[parts.test]`'s code in `settings.toml`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/test/helpers.py:alice_with_password`

```
assert found is not None
```

## `src/chatddx/test/helpers.py:found_alice`

```
assert found is not None
```

## `src/chatddx/test/helpers.py:found_alices_bench`

```
assert alice is not None
```

## `src/chatddx/test/world.py:edit`

```
assert old in text, f"{path} doesn't hold {old!r}"
```
