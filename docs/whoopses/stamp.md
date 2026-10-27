# Whoopses and asserts in `chatddx.stamp`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/stamp/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/stamp/code.py:Code.__init__`

```
assert isinstance(loaded, griffe.Module)
```

## `src/chatddx/stamp/code.py:Code.lines`

```
assert isinstance(obj.filepath, Path) and obj.lineno is not None
```

## `src/chatddx/stamp/code.py:Code.node`

```
assert isinstance(obj.filepath, Path) and obj.lineno is not None
```

## `src/chatddx/stamp/code.py:Code.source`

```
assert isinstance(obj.filepath, Path)
```

## `src/chatddx/stamp/index.py:_claims`

```
assert isinstance(module, griffe.Module)
```

## `src/chatddx/stamp/page.py:_Page.__init__`

```
assert isinstance(found, griffe.Module)
```

## `src/chatddx/stamp/page.py:_Page.function`

```
assert not isinstance(node, ast.ClassDef)
```

## `src/chatddx/stamp/page.py:_Page.heading`

```
assert isinstance(obj.filepath, Path)
```

## `src/chatddx/stamp/trace.py:Trace.of`

```
assert not isinstance(node, ast.ClassDef)
```
