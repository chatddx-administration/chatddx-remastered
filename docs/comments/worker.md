# Comments in `worker`

Written by `chatddx-dev index` from the comments in `[parts.worker]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/worker/publish.py:Publisher._drop`

```
# Policy: an item's row tells how it ended, so its deltas still held go unsaid.
```

## `src/chatddx/worker/test/test_worker.py:start`

```
# Accommodating for the request, which starts a run before it is queued: as it does, at
# an endpoint that answers.
```

## `src/chatddx/worker/worker.py:Worker._scored`

```
# Policy: scorer by scorer, so that the job keeps those it finished: queued again, it
# scores what is left.
```

## `src/chatddx/worker/worker.py:Worker._take`

```
# Policy: daemons, so that a server forced to quit, which skips stopping its
# worker, exits; the jobs it held are claimed again once lost.
```
