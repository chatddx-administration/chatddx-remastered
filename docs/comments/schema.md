# Comments in `schema`

Written by `chatddx-dev index` from the comments in `[parts.schema]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `frontend/src/lib/schema/form.ts:authored`

```
// Policy: a list of what people wrote, each item by its `author`, is one item a person.
```

## `frontend/src/lib/schema/form.ts:pruned`

```
// Policy: where a form shows every field, what is left empty is left out, an authored item
// holding nothing but its author included; a required field is kept, so that what it lacks is said.
```

## `frontend/src/lib/schema/form.ts:WORDED`

```
// Policy: a field goes by its name, but for those the portal words for clinicians.
```
