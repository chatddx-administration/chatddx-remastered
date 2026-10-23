# Whoopses and asserts in `chatddx.stamp`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/stamp/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

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
