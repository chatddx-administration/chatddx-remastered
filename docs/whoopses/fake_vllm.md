# Whoopses and asserts in `chatddx.fake_vllm`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/fake_vllm/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/fake_vllm/server.py:_Handler._released`

```
assert self.script is not None
```
