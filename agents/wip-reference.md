# Reference

`chatddx reference` writes `docs/reference/<package>.md` for each package in `settings.REFERENCED` from the code
(`src/chatddx/reference/`): each public name's signature and what it raises. It replaces `docs/<package>-api.md`,
identity and bench first.

## Where it stands among the common ways
- Reading the code: griffe (`src/chatddx/reference/code.py:Code`), the static loader behind mkdocstrings and
  `griffe check`, gives the names, what they are, their members, imports and line ranges. Their text, as the code
  spells it, is taken from the AST, since griffe respells it (`Literal['current']` for `Literal["current"]`).
- Rendering: its own, for the format below. griffe2md, the common renderer, writes about 490 lines for identity and
  says nothing of what is raised.
- What is raised: what pydoclint and ruff's DOC501 check a docstring's "Raises" against, a function's own `raise`
  statements, and with them its private helpers'.
- The workflow: Microsoft's API Extractor commits its API report the same way, and fails a build while it is behind.
- griffe is in the `docs` dependency group: a deployed chatddx goes without it.

## The workflow
- Before a commit, an agent runs `chatddx reference`, as it does `chatddx openapi`. `--check` writes nothing and fails
  while a reference is behind the code, and so does
  `src/chatddx/reference/test/test_reference.py:test_each_reference_is_as_chatddx_reference_writes_it`.
- A reference that doesn't exist yet is written whole, and signed off as a whole in review.
- After that, a change in the code is tagged above the lines it changes, in the template of AGENTS.md, rule 1, with
  `REFERENCE: ADD`, `REPLACE` or `REMOVE`. A human applies a tag by hand, which is their sign-off: the tag goes, and so
  do the lines it replaces or removes. Tags left unapplied are worked out anew on the next run from what is applied, so
  they neither pile up nor go stale, and a line edited by hand is tagged back to what the code says.

## What a reference holds
One entry for each name defined at the top of the package's modules, tests left out, that doesn't start with `_`, and
one for each public method, property and `__init__` of its classes, as `Class.name`, all sorted alphabetically whatever
their case, so that a class's members follow it:

````
## Seen.family
`src/chatddx/bench/seen.py:Seen.family`

* `found: int | str`
* ∟`Family`

Raises:

1. `NotFound`: no {word} {name!r} for {self.person.login} (through `Seen._named`)
2. `Ambiguous`: {word} {name!r} names {len(several)}; name one as OWNER/NAME (through `Seen._named`)
3. `NotFound`: no case {found} for {self.person.login}
````

- The heading holds the decorators, type parameters and bases, as written.
- A function's parameters, with `/` and `*` where the code has them, and `∟` its return type. `self` and `cls` are
  left out, and so is the first parameter of a function a class binds as an attribute, as `Bench` binds the writes,
  which is written once, as the class's method.
- A class's fields: annotated or assigned in its body, as written when on one line, and annotated on `self` in
  `__init__`. A constant as written when on one line, else its annotation.
- A docstring, as written. None of identity's or bench's names has one.

## What it says is raised
- The function's own `raise` statements, and those of the private helpers it calls, `(through <helper>)`, the one it
  calls, however deep the raise is: `_helper(…)`, and `self._helper(…)`, `cls._helper(…)` or `x._helper(…)` for a
  parameter `x` annotated with a class of the project.
- In the order the code reaches them, a helper's at the call; each raise once, where it is first reached.
- The message as the code writes it, an f-string's values as `{expr}`, a string constant's text in its place.
- An exception caught around a raise or a call isn't said, unless the handler raises it again.
- A class says what its validators raise, in a `ValidationError`, and what `__post_init__` raises.

Not said:
- What a public function or class it calls raises: its own entry says.
- What is raised without a `raise`: a `KeyError` from a subscript, pydantic's own validation, a library's errors.

What isn't said is said with an explicit `raise`, or with a docstring if AGENTS.md takes the exception suggested for
them.

## Open
- The other packages with a `docs/<package>-api.md`, and the references to them.
- The suggestions in AGENTS.md: the reference's place among the docs, its one writer, the step before a commit, and
  docstrings in the packages of `settings.REFERENCED`.
