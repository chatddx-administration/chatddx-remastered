# Comments in `chatddx.stamp`

Written by `chatddx stamp write` from the comments in `src/chatddx/stamp/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/stamp/code.py:Code._runtime`

```
# Compromise: the project is read, never imported, which would take its environment;
# a library is imported, for the bases of the exceptions it raises.
```

## `src/chatddx/stamp/code.py:File.segment`

```
# Optimization: ast.get_source_segment, but over lines split once, where it splits
# the whole source on each call.
```

## `src/chatddx/stamp/index.py:_SCANNED`

```
# Compromise: what isn't Python is read by its strings and comments alone: a body in
# dollar quotes is read as SQL, as a function's body is, and an E'' string's \' throws
# the reading off.
```
