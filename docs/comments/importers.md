# Comments in `chatddx.importers`

Written by `chatddx stamp write` from the comments in `src/chatddx/importers/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/importers/o11n.py:_error`

```
# Accommodating for o11n's report: a part it couldn't gather holds only the error.
```

## `src/chatddx/importers/o11n.py:_HOST_ENV`

```
# Policy: o11n.vllm sets these on every server to find the model, the GPU and CUDA,
# which the runtime closure covers: where an engine runs, not what it is.
```

## `src/chatddx/importers/o11n.py:REPORT`

```
# Dependency: the report o11n.vllm writes about the vLLM servers on one host
# (Kompismoln/o11n, nixos/vllm-report.py).
```

## `src/chatddx/importers/test/test_o11n.py:server`

```
# Accommodating for a discovered fact: a report as o11n.vllm's vllm-report gave it for
# one server, pelle's qwen3-8b.
```
