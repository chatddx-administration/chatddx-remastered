# Whoopses and asserts in `chatddx.catalog`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/catalog/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/catalog/model.py:About.of`

```
assert e.value is not None
```

```
assert e.person is not None
```

## `src/chatddx/catalog/read.py:tags_given`

```
assert entry.value is not None
```

## `src/chatddx/catalog/threads.py:_shape`

```
assert r is not None
```
