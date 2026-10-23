# Comments in `chatddx.conftest`

Written by `chatddx stamp write` from the comments in `src/chatddx/conftest.py`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/conftest.py:cheap_hashing`

```
# Optimization: passwords are hashed as cheaply as argon2 allows: the tests check what
# is hashed, not how hard it is to reverse.
```

## `src/chatddx/conftest.py:described`

```
# Duplication: as src/chatddx/cli.py:_openapi makes it.
```

## `src/chatddx/conftest.py:plan`

```
# Policy: module-scoped, as tests add to its registry.
```

## `src/chatddx/conftest.py:shipped_test_tools`

```
# Dependency: the test World's tools are the runner's test tools
# (worlds/test/_data/factors.toml), shipped for the whole session so that planning takes
# their entry points.
```

## `src/chatddx/conftest.py:unsynced_commits`

```
# Optimization: what a test writes needn't outlive a crash, so no commit waits for the
# WAL to reach the disk.
```
