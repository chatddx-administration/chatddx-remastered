# Comments in `library`

Written by `chatddx-dev index` from the comments in `[parts.library]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `frontend/src/islands/library.ts:checked`

```
// Policy: a JSON box says as it is typed in what keeps it from being sent, and the form
// isn't sent while it does, rather than coming back refused.
```

## `frontend/src/islands/library.ts:enhanced`

```
// Policy: the text box stays the form's, so that it posts as it does without scripts; an editor writes into it only
// what is changed in it, so that a form sent as it is writes nothing.
```

## `frontend/src/lib/library/editors.ts:segsOf`

```
// Dependency: an either-field's text box and its "as." select, as src/chatddx/portal/templates/fields.html draws them.
```
