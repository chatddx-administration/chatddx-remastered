# Comments in `compose`

Written by `chatddx-dev index` from the comments in `[parts.compose]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `frontend/src/islands/Compose.svelte:drafts`

```
// Policy: a text's translations follow it as it is typed, so the translations are drafted on the server alongside
// the chunks, and aren't typed in meanwhile.
```

## `frontend/src/lib/compose/Settings.svelte:SHOWN`

```
// Policy: the guidance of an output and a toolset is text, drafted with the other texts and translated with them.
```

## `frontend/src/lib/compose/drafting.ts:STANDS_FOR`

```
// Dependency: src/chatddx/factors/request.py:compile_request refuses a guidance inserted in both the instructions and the
// prompt, and fills one in only where it is held.
```

## `frontend/src/lib/compose/drafting.ts:TEXTS`

```
// Dependency: src/chatddx/factors/request.py:texts orders a recipe's texts by these parts.
```

## `src/chatddx/portal/compose.py:_set`

```
# Accommodating for the forms, which show a field that is set: a default left out is
# filled in again where it is read, to the same digest.
```
