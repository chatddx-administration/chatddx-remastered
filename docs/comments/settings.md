# Comments in `chatddx.settings`

Written by `chatddx stamp write` from the comments in `src/chatddx/settings.py`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/settings.py:SERVE_GRACE`

```
# Policy: how long a server stopping waits on its open responses, a run's event stream
# among them, which ends only with the run's job, before it cuts them off.
```

## `src/chatddx/settings.py:WORKER_DEADLINE`

```
# Policy: within the stop timeout of the service that runs the worker, TimeoutStopSec in
# nix/module.nix.
```

## `src/chatddx/settings.py:WORKER_JOBS`

```
# Policy: bounds a worker's threads, and its connections at 1 + 2 per job
# (src/chatddx/worker/worker.py:Worker._work).
```
