# Comments in `index`

Written by `chatddx-dev index` from the comments in `[parts.index]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `dev/src/chatddx_dev/index/__init__.py:_files`

```
# Policy: what git keeps or would add, so that what a tool writes and git ignores, such as
# frontend/src/lib/api/schema.d.ts, isn't read, and what [index] left_out names neither.
```

## `dev/src/chatddx_dev/index/anchored.py:SCANNED`

```
# Compromise: what isn't Python is read by its strings and comments alone: a body in
# dollar quotes is read as SQL, as a function's body is, and an E'' string's \' throws
# the reading off.
```

## `dev/src/chatddx_dev/index/bash.py:_doc`

```
# Policy: a block of comments alone on their lines, its shellcheck directives left out:
# the one a script begins with, from its first line or the one after its shebang, or the
# one right above a function.
```

## `dev/src/chatddx_dev/index/bash.py:_environment`

```
# Policy: an assignment that reads what it assigns, as X=${X:-x} does, takes it from
# the environment still.
```

## `dev/src/chatddx_dev/index/bash.py:_OWN`

```
# Policy: what bash sets itself, or any environment holds, is no part of a script's surface.
```

## `dev/src/chatddx_dev/index/bash.py:LEGEND`

```
# Duplication: surface renders the entries this tells how to read.
```

## `dev/src/chatddx_dev/index/code.py:Code._runtime`

```
# Compromise: the project is read, never imported, which would take its environment;
# a library is imported, for the bases of the exceptions it raises.
```

## `dev/src/chatddx_dev/index/code.py:File.segment`

```
# Optimization: ast.get_source_segment, but over lines split once, where it splits
# the whole source on each call.
```

## `dev/src/chatddx_dev/index/frontend.py:LEGEND`

```
# Duplication: frontend/scripts/facts.mjs renders the entries this tells how to read.
```
