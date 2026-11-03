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

## `frontend/src/lib/compose/Preview.svelte`

```
// Policy: besides Update, it compiles as it opens on nothing compiled, and as it shows another language's tab than it
// was compiled in, as it would show nothing or another language otherwise.
```

## `frontend/src/lib/compose/Preview.svelte:saved`

```
// Policy: what it sends is marked against what the version drafted on sends in the same language, saved; saving
// makes the next of them.
```

## `frontend/src/lib/compose/Preview.svelte:TINTS`

```
// Policy: what a message holds of its own part stands unmarked, what is put into it is tinted.
```

## `frontend/src/lib/compose/Settings.svelte`

```
<!-- Policy: a budget the model's facts refuse is offered only to be taken out, as it compiles to nothing else. -->
```

## `frontend/src/lib/compose/Settings.svelte:followed`

```
// Dependency: src/chatddx/factors/request.py:landings follows the level reasoning lands at, or else the default.
```

## `frontend/src/lib/compose/Texts.svelte:pairedNow`

```
// Policy: what is listed rather than paired follows the texts the server last said, so that a text being typed
// doesn't move between the two meanwhile.
```

## `frontend/src/lib/compose/diffing.ts:overlaid`

```
// Policy: a message changed word by word keeps its runs, each cut where the words added start and end, and what was taken
// out stands where it was; a slot or an appendix is shown once, where it starts.
```

## `frontend/src/lib/compose/diffing.ts:pretty`

```
// Policy: the body as sent is JSON but for its texts' line breaks, which break its lines, so that a message reads as it
// is written.
```

## `frontend/src/lib/compose/diffing.ts:rows`

```
// Policy: messages are matched whole, by role and text, so that a message added or taken out marks itself alone; a run
// of them taken out where as many are added is each changed in its place, word by word.
```

## `frontend/src/lib/compose/drafting.ts:paired`

```
// Dependency: src/chatddx/factors/request.py:own_texts, the texts of the prose Compose pairs with their translations;
// the rest of what it finds, a schema's and the tools' among them, is listed as it is.
```

## `frontend/src/lib/compose/drafting.ts:restaled`

```
// Policy: a translation the server carried over to a text that changed is to be looked over, as it was written for
// the text before; the client alone keeps that, till it is typed in or said to read right.
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
