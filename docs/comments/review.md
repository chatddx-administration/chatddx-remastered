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

## `frontend/src/lib/review/Expected.svelte:step`

```
// Policy: the fields hold the version shown, so that Save makes it the latest; what was
// typed over the one shown is replaced only once confirmed.
```

## `frontend/src/lib/review/Faring.svelte`

```
// Policy: read once the section is near view, as most visits to a case look at its expectation alone.
<<<<<<< signed
=======
```

## `frontend/src/lib/review/Faring.svelte:AGAIN`

```
// Policy: read again so long after while a run of the case is under way, so that what it scores comes in
// without a stream held open for each of its runs.
>>>>>>> @stamp
```

## `frontend/src/lib/review/Measuring.svelte`

```
// Policy: what was measured stays as the column closes, so that it slides out whole.
```

## `frontend/src/lib/review/Measuring.svelte:PAGE`

```
// Policy: so many texts at a time, so that a case read thousands of times opens at once.
```

## `frontend/src/lib/review/edited.svelte.ts:Edited`

```
// Policy: the page's Save writes each part that holds something unsaved, by rank, and stops at
// the first refused; what was written stays written, so saving again writes what is left.
```

## `frontend/src/lib/review/faring.ts:below`

```
// Policy: the share of the other cases below this one, a tie counting as half, so that a case among equals sits mid-way.
```

## `frontend/src/lib/review/faring.ts:BINS`

```
// Policy: so many bins between 0 and 1, so that a mean of four replicates falls on one of its own.
```

<<<<<<< signed
=======
## `frontend/src/lib/review/faring.ts:ticks`

```
// Policy: replicates of a value side by side, so that four alike on a metric that scores 0 or 1 show as four.
```

>>>>>>> @stamp
## `frontend/src/lib/review/measure.svelte.ts:segments`

```
// Duplication: src/chatddx/portal/scores.py:_segments marks a text alike.
```
