# Comments in `chatddx.stamp`

Written by `chatddx stamp write` from the comments in `src/chatddx/stamp/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

<<<<<<< signed
## `src/chatddx/stamp/__init__.py:documents`

```
# Duplication: scripts/refcheck.py:sources, which runs without chatddx.
```

=======
>>>>>>> @stamp
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

## `src/chatddx/stamp/markers.py:_CLOSING`

```
# Policy: never spelled whole, so that a search for it finds the stamps pending alone.
```
<<<<<<< signed

## `src/chatddx/stamp/test/test_stamp.py:needs_git`

```
# Accommodating for nix's sandbox, which checks the package without git.
```
=======
>>>>>>> @stamp
