# `stamp`

Written by `chatddx-dev index` from `[parts.stamp]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

Python:

```
## `<name>` `@<decorator>` `[<type parameters>]` `(<bases>)`
`<file>:<qualified name>`

* `<parameter or field>: <type> = <default>`
* ∟`<return type>`

Raises:
1. `<exception>`: `<arguments>` (from `<exception caught>`, through `<private helper>`, in a `ValidationError`)

Finds:
1. `<code>`: `<message>` (`<level>`, from `<exception caught>`, through `<private helper>`)
```

- A constant or a type alias is its definition instead of bullets; a class and its `__init__` leave out ∟, and a method its instance; `*`: the parameters after it are keyword-only, `/`: those before it positional-only.
- Raises and Finds are the function's own and its private helpers', in the order the code reaches them, each once, a `Whoops` left out; what a public function it calls raises is in that function's entry.
- Text is quoted, a value in it as `{<expression>}`, and an argument that isn't text is as written; a finding is a warning unless it gives its level.

- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `check`
`dev/src/chatddx_dev/stamp/__init__.py:check`

Fails, saying which, while a doc, an index or a catalog holds a conflict that isn't
a stamp, or a stamp that isn't closed.

* ∟`None`

Raises:
1. `SystemExit`: `"stamp: {e}"` (from `ValueError`)

## `docs`
`dev/src/chatddx_dev/stamp/__init__.py:docs`

* `base: str`
* `check: bool = False`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp docs: git {args[0]}: {e.stderr.strip()}"` (from `subprocess.CalledProcessError`, through `_git`)
2. `SystemExit`: `"stamp docs: {_shown(path)}: {e}"` (from `ValueError`)
3. `SystemExit`: `"stamp docs: {listed} behind: run ./dev/write.sh stamps"`

## `documents`
`dev/src/chatddx_dev/stamp/__init__.py:documents`

* ∟`list[Path]`

## `pending`
`dev/src/chatddx_dev/stamp/__init__.py:pending`

* ∟`None`

Raises:
1. `SystemExit`: `"stamp pending: {e}"` (from `ValueError`)
2. `SystemExit`: `1`

## `reflow`
`dev/src/chatddx_dev/stamp/__init__.py:reflow`

* `check: bool`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp reflow: {e}"` (from `ValueError`)
2. `SystemExit`: `done.returncode`
3. `SystemExit`: `"stamp reflow: {name}: {done.stderr.strip()}"` (through `_prettier`)
4. `SystemExit`: `"stamp reflow: {listed} unformatted: run chatddx-dev stamp reflow"`
