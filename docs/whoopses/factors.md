# Whoopses and asserts in `chatddx.factors`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/factors/`, its tests left out, each under its file and the name it is in; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/factors/base.py:Component.kind_name`

```
assert isinstance(kind, str)
```

## `src/chatddx/factors/scoring.py:fill_text`

```
assert op == "text@1"
```

## `src/chatddx/factors/select.py:_Parser.filter`

```
assert isinstance(step, Name | Index)
```

## `src/chatddx/factors/select.py:split`

```
assert op == "lines@1"
```
