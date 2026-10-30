# `rig`

Written by `chatddx-dev index` from `[parts.rig]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

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

## `entry` `[T: Versioned]`
`src/chatddx/rig.py:entry`

* `shipped: Mapping[str, T]`
* `entry_point: str`
* `version: int`
* ∟`T`

Raises:
1. `LookupError`: `"{entry_point} isn't shipped with {running}, only {", ".join(sorted(shipped)) or "nothing"}"`
2. `LookupError`: `"{entry_point} is at version {found.version} in {running}, not {version}"`

## `rig`
`src/chatddx/rig.py:rig`

* ∟`Code`

## `Versioned` `(Protocol)`
`src/chatddx/rig.py:Versioned`

## `Versioned.version` `@property`
`src/chatddx/rig.py:Versioned.version`

* ∟`int`
