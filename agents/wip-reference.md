# Reference

`chatddx reference` writes `docs/reference/<package>.md` for each package in `settings.REFERENCED` from the code
(`src/chatddx/reference/`): each public name's signature and what it raises. It replaces `docs/<package>-api.md`,
identity and bench first.

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
- The names defined at the top of the package's modules, tests left out, that don't start with `_`, sorted
  alphabetically whatever their case. `__all__` isn't read: 9 of 20 packages have none.
- A function's signature as the code writes it, decorators included. A function a class binds as an attribute, as
  `Bench` binds the writes, is written once, as the class's method, without its first parameter.
- A class's decorators and bases, its fields (annotated or assigned in its body, and annotated on `self` in
  `__init__`), its properties, its constructor (`__init__`, as `Name(…)`) and its public methods, alphabetically.
- A constant's annotation, and its value when the code writes it on one line.
- A docstring, as written. None of identity's or bench's names has one.

## What it says is raised
- Each `raise` with its message: an f-string's values as `<expr>`, a string constant's text in its place.
- What a private callee raises, as the caller's own; a public callee by name, in one line: "raises what `X`, `Y`
  raise". A name in another package is written as that package exports it, `store.Catalog.adopt`.
- Calls are followed through what the code annotates: parameters, fields, `self.x: T` in `__init__`, properties' and
  functions' return types, and locals assigned from these.
- An exception caught around a call or a raise isn't said, unless the handler raises it again.
- A class says what its validators raise, in a `ValidationError`, and what `__post_init__` raises.

Not seen:
- What is raised without a `raise`: a `KeyError` from a subscript, pydantic's own validation, a library's errors.
- Calls through an unannotated value, a Protocol (whose stubs raise nothing), a callback, `super()` or a lookup such
  as `KINDS[word]`.
- Whether a caller's arguments rule a callee's raise out: a callee is named whenever any of its raises can escape.

What isn't seen is said with an explicit `raise`, or with a docstring if AGENTS.md takes the exception suggested for
them.

## Open
- The other packages with a `docs/<package>-api.md`, and the references to them.
- The suggestions in AGENTS.md: the reference's place among the docs, its one writer, the step before a commit, and
  docstrings in the packages of `settings.REFERENCED`.
