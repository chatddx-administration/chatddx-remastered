# Whoopses and asserts in `chatddx.test`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/test/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

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
