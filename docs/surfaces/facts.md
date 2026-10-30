# `facts`

Written by `chatddx-dev index` from `[parts.facts]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

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

## `BUNDLED`
`src/chatddx/facts/models.py:BUNDLED`

`BUNDLED = Path(__file__).with_name("models.toml")`

## `check_pairs`
`src/chatddx/facts/lint.py:check_pairs`

* `registry: Registry`
* `facts: Facts`
* `digests: Iterable[str] | None = None`
* ∟`list[Finding]`

Finds:
1. `facts.missing`: `"no facts about %(name)s, so model-level checks were skipped"` (`info`, through `_pair`)
2. `facts.reasoning_unmatched`: `"the configuration's reasoning settings match none of the model's reasoning levels"` (through `_pair`)
3. `facts.budget_refused`: `model.reasoning.budget.refused` (through `_pair`)
4. `facts.output_refused`: `reason` (through `_pair`)
5. `facts.output_note`: `note` (`info`, through `_pair`)
6. `facts.sampling_unmatched`: `"the configuration's sampling is what the facts recommend for %(others)s, not for %(name)s"` (through `_pair`)

## `Facts` `(Frozen)`
`src/chatddx/facts/models.py:Facts`

* `models: dict[str, ModelFacts] = Field(default_factory=dict)`

## `Facts.about`
`src/chatddx/facts/models.py:Facts.about`

* `digest: str`
* `get: Resolver`
* ∟`ModelFacts | None`

## `Facts.load` `@classmethod`
`src/chatddx/facts/models.py:Facts.load`

* `*paths: Path`
* ∟`Self`

Raises:
1. `ValueError`: `"{path}: facts have only 'model' tables"`
2. `ValueError`: `"{name!r} has facts in more than one file"`

## `Facts.of` `@classmethod`
`src/chatddx/facts/models.py:Facts.of`

* `found: Iterable[ModelFacts]`
* ∟`Self`

## `Facts.served`
`src/chatddx/facts/models.py:Facts.served`

* `engines: Mapping[str, Mapping[str, Component]]`
* ∟`Self`

## `lints`
`src/chatddx/facts/lint.py:lints`

* `registry: Registry`
* `facts: Facts`
* `digests: Collection[str]`
* `languages: Languages | None = None`
* `engines: Mapping[str, str] | None = None`
* ∟`list[Finding]`

## `reasons`
`src/chatddx/facts/lint.py:reasons`

* `facts: Facts`
* `registry: Registry`
* ∟`Reasons`
