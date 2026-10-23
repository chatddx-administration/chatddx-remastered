# Whoopses and asserts in `chatddx.store`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/store/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/store/catalog.py:Catalog._insert`

```
assert row is not None
```

## `src/chatddx/store/catalog.py:Catalog.adopt`

```
assert row is not None
```

## `src/chatddx/store/catalog.py:Catalog.create`

```
assert row is not None
```

## `src/chatddx/store/catalog.py:Rows.runs_started`

```
assert row is not None
```

## `src/chatddx/store/people.py:People.add`

```
assert row is not None
```

## `src/chatddx/store/queue.py:Queue.claim`

```
assert claimed is not None
```

## `src/chatddx/store/queue.py:Queue.put`

```
assert row is not None
```

## `src/chatddx/store/queue.py:Queue.standing`

```
assert row is not None
```

## `src/chatddx/store/texts.py:Texts.typed_since`

```
assert row is not None
```
