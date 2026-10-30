# Comments in `paging`

Written by `chatddx-dev index` from the comments in `[parts.paging]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `frontend/src/lib/paging/Finding.svelte:query`

```
// Policy: a list in the browser is found in as it is typed, and its Enter sends no form it
// sits in; one on the server when its search is sent.
```

## `frontend/src/lib/paging/Pages.svelte:at`

```
// Policy: a list in the browser knows its last page; one on the server only whether
// there is a next.
```

## `frontend/src/lib/paging/paging.ts:found`

```
// Dependency: a list as the pages rendered on the server find in and page it
// (src/chatddx/portal/templates/base.html): the rows that say every word typed, whatever
// its case, a page of them at a time.
```
