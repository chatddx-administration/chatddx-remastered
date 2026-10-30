# `markers`

Written by `chatddx-dev index` from `[parts.markers]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

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

## `applied`
`src/chatddx/markers.py:applied`

* `text: str`
* ∟`list[str]`

Raises:
1. `ValueError`: `"line {n}: a conflict marker that isn't a stamp's"` (through `_sides`)
2. `ValueError`: `"line {opened}: a stamp isn't closed"` (through `_sides`)

## `applied_lines`
`src/chatddx/markers.py:applied_lines`

* `text: str`
* ∟`list[tuple[int, str]]`

Raises:
1. `ValueError`: `"line {n}: a conflict marker that isn't a stamp's"` (through `_sides`)
2. `ValueError`: `"line {opened}: a stamp isn't closed"` (through `_sides`)

## `PENDING`
`src/chatddx/markers.py:PENDING`

`PENDING = …`

## `restamped`
`src/chatddx/markers.py:restamped`

* `base: str | None`
* `current: str`
* ∟`str`

## `signed`
`src/chatddx/markers.py:signed`

* `text: str`
* ∟`list[str]`

Raises:
1. `ValueError`: `"line {n}: a conflict marker that isn't a stamp's"` (through `_sides`)
2. `ValueError`: `"line {opened}: a stamp isn't closed"` (through `_sides`)

## `stamped`
`src/chatddx/markers.py:stamped`

* `current: str | None`
* `written: str`
* ∟`str`

## `stamps`
`src/chatddx/markers.py:stamps`

* `text: str`
* ∟`list[tuple[str, ...]]`
