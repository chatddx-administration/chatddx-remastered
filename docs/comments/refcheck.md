# Comments in `refcheck`

Written by `chatddx-dev index` from the comments in `[parts.refcheck]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `dev/src/chatddx_dev/refcheck/__init__.py:_ELSEWHERE_BEFORE`

```
# Accommodating for references the docs make on purpose to what isn't here: another
# repository's files, a repository at a commit, an earlier commit's code, and files
# planned or gone.
```

## `dev/src/chatddx_dev/refcheck/__init__.py:_off_main`

```
# Accommodating for a checkout without git or main, such as nix's, where commits go
# unchecked, and a shallow one, which holds main only so far back: a commit it doesn't
# hold, or one older than the oldest of main it holds, is taken to be on main.
```
