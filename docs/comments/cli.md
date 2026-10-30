# Comments in `cli`

Written by `chatddx-dev index` from the comments in `[parts.cli]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

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
