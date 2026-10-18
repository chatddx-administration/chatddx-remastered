# `chatddx.facts`

Written by `chatddx reference` from `src/chatddx/facts/`: each public name, sorted, with its parameters or fields,
```
REFERENCE: REPLACE
replace the line below with these
---
`∟` its return type, what it raises and what it finds.
```
`∟` its return type, and what it raises.

- `*`: the parameters after it are keyword-only; `/`: those before it are positional-only. A function a
  class binds as an attribute is its method: its first parameter, the instance, is left out.
- Raises: the function's own `raise` statements and its private helpers' (through `<helper>`), in the order
  the code reaches them, each once. What the public functions it calls raise is in their own entries.
- A message is quoted, with the values of the code that raises it as `{expr}`; an argument that isn't text is
  as written, and from `<exception>` when it is the exception caught.
```
REFERENCE: ADD
add these lines here
---
- Finds: each `Finding` it makes, as `code`: message, followed as Raises are; a warning unless it says info.
```

## BUNDLED
`src/chatddx/facts/models.py:BUNDLED`

* `BUNDLED = Path(__file__).with_name("models.toml")`

## check_pairs
`src/chatddx/facts/lint.py:check_pairs`

* `registry: Registry`
* `facts: Facts`
* `digests: Iterable[str] | None = None`
* ∟`list[Finding]`
```
REFERENCE: ADD
add these lines here
---

Finds:

1. `facts.missing`: "no facts about {name!r}, so model-level checks were skipped" (info, through `_pair`)
2. `facts.reasoning_unmatched`: "the configuration's reasoning settings match none of the model's reasoning levels" (through `_pair`)
3. `facts.budget_refused`: model.reasoning.budget.refused (through `_pair`)
4. `facts.output_refused`: reason (through `_pair`)
5. `facts.output_note`: note (info, through `_pair`)
6. `facts.sampling_unmatched`: "the configuration's sampling is what the facts recommend for {', '.join(others)}, not for {name}" (through `_pair`)
```

## Facts `(Frozen)`
`src/chatddx/facts/models.py:Facts`

* `models: dict[str, ModelFacts] = Field(default_factory=dict)`

## Facts.about
`src/chatddx/facts/models.py:Facts.about`

* `digest: str`
* `get: Resolver`
* ∟`ModelFacts | None`

## Facts.load `@classmethod`
`src/chatddx/facts/models.py:Facts.load`

* `*paths: Path`
* ∟`Self`

Raises:

1. `ValueError`: "{path}: facts have only 'model' tables"
2. `ValueError`: "{name!r} has facts in more than one file"

## Facts.of `@classmethod`
`src/chatddx/facts/models.py:Facts.of`

* `found: Iterable[ModelFacts]`
* ∟`Self`

## lints
`src/chatddx/facts/lint.py:lints`

* `registry: Registry`
* `facts: Facts`
* `digests: Collection[str]`
* `languages: Languages | None = None`
* ∟`list[Finding]`

## reasons
`src/chatddx/facts/lint.py:reasons`

* `facts: Facts`
* `registry: Registry`
* ∟`Reasons`
