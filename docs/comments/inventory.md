# Comments in `inventory`

Written by `chatddx-dev index` from the comments in `[parts.inventory]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/inventory/check.py:broken`

```
# Policy: Checked as a process starts and before the World changes, as
# src/chatddx/bench/seen.py:Seen.served relies on it.
```

## `src/chatddx/inventory/inventory.py:Inventory.serving`

```
# Policy: De facto refusal mechanism for
# src/chatddx/runner/score.py:judge_at and src/chatddx/bench/seen.py:Seen.at
```
