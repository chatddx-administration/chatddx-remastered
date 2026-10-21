# Comments in `chatddx.worker`

Written by `chatddx stamp write` from the comments in `src/chatddx/worker/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

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
