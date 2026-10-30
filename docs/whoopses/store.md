# Whoopses and asserts in `store`

Written by `chatddx-dev index` from the `raise Whoops` and `assert` statements in `[parts.store]`'s code in `settings.toml`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

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
