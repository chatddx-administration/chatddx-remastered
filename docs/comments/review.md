# Comments in `review`

Written by `chatddx-dev index` from the comments in `[parts.review]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `frontend/src/lib/review/Evaluation.svelte:halt`

```
// Policy: as on the run page, a run with nothing left under way is halted already.
```

## `frontend/src/lib/review/Evaluation.svelte:PATIENCE`

```
// Policy: the values shown stay till the next evaluation's have come, so that the table doesn't empty and
// jump between them; one under way shows as soon as it has had a moment to tell what it holds.
```

## `frontend/src/lib/review/Evaluation.svelte:WATCHED`

```
// Policy: so many streams at once and no more, so that the six connections a browser holds to a host over HTTP/1.1
// leave room for the page's own requests, a halt's among them; a stream joined late tells the rows before it.
```

## `frontend/src/lib/review/Expected.svelte:step`

```
// Policy: the fields hold the version shown, so that Save makes it the latest; what was
// typed over the one shown is replaced only once confirmed.
```

## `frontend/src/lib/review/edited.svelte.ts:Edited`

```
// Policy: the page's Save writes each part that holds something unsaved, by rank, and stops at
// the first refused; what was written stays written, so saving again writes what is left.
```
