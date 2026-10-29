# Comments in `chatddx.cli`

Written by `chatddx stamp write` from the comments in `src/chatddx/cli.py`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/cli.py:_costs`

```
# Compromise: as in _stamp, for pytest, which chatddx.test.costs is a plugin of.
```

## `src/chatddx/cli.py:_refcheck`

```
# Compromise: as in _stamp, for chatddx.stamp, which it reads the docs with.
```

## `src/chatddx/cli.py:_stamp`

```
# Compromise: griffe, which chatddx.stamp reads the code with, is a development
# dependency, which a deployed chatddx goes without.
```

## `src/chatddx/cli.py:_worker.stop`

```
# Policy: as the repl's Ctrl-C, the first press ends the runs after the items under
# way, the second hangs those up at once and the third kills.
```

## `src/chatddx/cli.py:DATA`

```
# Policy: a World's data set is where the World itself doesn't read it; init-data's by
# default.
```
