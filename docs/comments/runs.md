# Comments in `runs`

Written by `chatddx-dev index` from the comments in `[parts.runs]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `frontend/src/lib/runs/events.ts:watch`

```
// Accommodating for EventSource, where a lost connection is an "error" too, one without data.
```

## `frontend/src/lib/runs/titles.ts:caseTitle`

```
// Dependency: a case's title as src/chatddx/portal/titles.py:display_case says it.
```

## `frontend/src/lib/runs/titles.ts:runTitle`

```
// Dependency: a run's title as the portal's macros.html:run_title says it.
```
