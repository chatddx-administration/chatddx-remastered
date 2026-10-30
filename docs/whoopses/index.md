# Whoopses and asserts in `index`

Written by `chatddx-dev index` from the `raise Whoops` and `assert` statements in `[parts.index]`'s code in `settings.toml`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `dev/src/chatddx_dev/index/anchored.py:_claims`

```
assert isinstance(module, griffe.Module)
```

## `dev/src/chatddx_dev/index/anchored.py:read`

```
assert code is not None, "a Python file is read with the package it is in"
```

## `dev/src/chatddx_dev/index/code.py:Code.__init__`

```
assert isinstance(loaded, griffe.Module)
```

## `dev/src/chatddx_dev/index/code.py:Code.lines`

```
assert isinstance(obj.filepath, Path) and obj.lineno is not None
```

## `dev/src/chatddx_dev/index/code.py:Code.node`

```
assert isinstance(obj.filepath, Path) and obj.lineno is not None
```

## `dev/src/chatddx_dev/index/code.py:Code.source`

```
assert isinstance(obj.filepath, Path)
```

## `dev/src/chatddx_dev/index/surfaces.py:_Page.__init__`

```
assert isinstance(found, griffe.Module)
```

## `dev/src/chatddx_dev/index/surfaces.py:_Page.function`

```
assert not isinstance(node, ast.ClassDef)
```

## `dev/src/chatddx_dev/index/surfaces.py:_Page.heading`

```
assert isinstance(obj.filepath, Path)
```

## `dev/src/chatddx_dev/index/trace.py:Trace.of`

```
assert not isinstance(node, ast.ClassDef)
```
