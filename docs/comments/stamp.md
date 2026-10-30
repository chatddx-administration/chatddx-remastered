# Comments in `stamp`

Written by `chatddx-dev index` from the comments in `[parts.stamp]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `dev/src/chatddx_dev/stamp/__init__.py:reflow`

```
# Policy: prettier reads a stamp's markers as markdown, so a doc holding stamps pending is
# reflowed a side at a time, the side last stamped and the side written now, each as a doc
# of its own, and stamped again from the two.
```

```
# Accommodating for prettier, which lists what differs at its log level, so that any
# quieter level lists nothing and passes.
```
