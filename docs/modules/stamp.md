# Stamp

`chatddx stamp` writes `docs/surfaces/<package>.md` for each package in `settings.STAMPED` from the code
(`src/chatddx/stamp/`): each public name's signature, what it raises and what it finds, and what changed since a human
last stamped it. `settings.STAMPED` holds the solidified packages, those with a `docs/modules/<package>.md` (AGENTS.md,
"Development stages").

## The workflow

- Before a commit, an agent runs `chatddx stamp`, as it does `chatddx openapi`, and `scripts/check.sh` runs
  `chatddx stamp --check` (AGENTS.md, "Pre-commit checklist"), which writes nothing and fails while a surface is behind
  the code, as `src/chatddx/stamp/test/test_stamp.py:test_each_surface_is_as_chatddx_stamp_writes_it` does. Stamps left
  pending don't fail it, since they wait for a human, not for the code; it says how many each surface has.
- A surface that doesn't exist yet is written whole, and stamped as a whole in review.
- A change in the generator's format is written whole too, deleting the surfaces and running `chatddx stamp`, and only
  while `chatddx stamp --check` passes with no stamp pending: the signed sides are then the code as the old format
  writes it, so nothing goes unstamped.
- After that, a change in the code is written in place of the lines it changes as a git conflict
  (`src/chatddx/stamp/markers.py:stamped`): `<<<<<<< signed`, the lines as last stamped, `=======`, what the code says
  now, `>>>>>>> @stamp`. A human takes the code's side, which is their stamp. Stamps left pending are worked out anew on
  the next run from the signed sides, so they neither pile up nor go stale, and a line edited by hand is stamped back to
  what the code says. A conflict marker that isn't a stamp's, from a merge, is refused.
- `.prettierignore` leaves `docs/surfaces/` out, since prettier reads a stamp as markdown: `=======` underlines the line
  above it as a heading, `>>>>>>>` is a quote seven deep. The root `.prettierrc` is there for conform.nvim, which runs
  prettier where it finds one, the only place prettier reads `.prettierignore` from.
- Only the entries are stamped. What comes before the first, the title and a line saying how to read it, is the
  generator's own and written as it is: they change with the generator, in its commits, and aren't stamped.

## What a surface holds

Its header points to the legend, `docs/surfaces.md`, which says how to read it: what `∟`, `*`, `/`, "through" and a
quoted message mean, that a bound method leaves out its instance, that a public callee's raises are in its own entry,
and what a pending stamp is.

One entry for each name defined at the top of the package's modules, tests left out, that doesn't start with `_`, and
one for each public method, property and `__init__` of its classes, as `Class.name`, all sorted alphabetically whatever
their case, so that a class's members follow it:

```
## `Seen.family`
`src/chatddx/bench/seen.py:Seen.family`

* `found: int | str`
* ∟`Family`

Raises:
1. `NotFound`: `"no {word} {name!r} for {self.person.login}"` (through `Seen._named`)
2. `Ambiguous`: `"{word} {name!r} names {len(several)}; name one as OWNER/NAME"` (through `Seen._named`)
3. `NotFound`: `"no case {found} for {self.person.login}"`
```

- What is quoted from the code is in code, so that markdown reads none of it: `Seen.__init__` in a heading, or
  `{cls.__name__}` in a message, would be bold. Code holding backticks is fenced with more of them.
- The heading holds the name, and the decorators, type parameters and bases, as written; a decorator written on more
  than one line as its callable and first argument, `@router.post("/runs/{run}/again", …)`. A name two modules of the
  package define is headed with its module, `runs.EVENTS`.
- A function's parameters, with `/` and `*` where the code has them, and `∟` its return type, which a class's `__init__`
  leaves out: calling the class gives one of it, and no class of `settings.STAMPED` has a `__new__` or a metaclass that
  gives another. `self` and `cls` are left out, and so is the first parameter of a function a class binds as an
  attribute, as `Bench` binds the writes, which is written once, as the class's method.
- A class's fields: annotated or assigned in its body, as written when on one line, and annotated on `self` in
  `__init__`. A constant or a type alias, without a bullet, since it is neither: as written when on one line. Else the
  annotation and the head of the value: `= Field(…)`, `= {…}`, `= Literal[…]`.
- A docstring, as written (AGENTS.md, "4. When and how to write a docstring").

## Raises

- The function's own `raise` statements, and those of the private helpers it calls, `(through <helper>)`, the one it
  calls, however deep the raise is: `_helper(…)`, and `self._helper(…)`, `cls._helper(…)` or `x._helper(…)` for a
  parameter `x` annotated with a class of the project.
- In the order the code reaches them, a helper's at the call; each raise once, where it is first reached.
- The arguments as the code writes them: text quoted, an f-string's values as `{expr}` and a string constant's text in
  its place; anything else as written, `` `HTTPException`: `422, "only a configuration answers"` ``. A raise in an
  `except` that uses the exception caught says `from` it: `` `ValueError`: `str(e)` (from `LookupError`) ``.
- A function that returns the exception raised is a helper:
  `` `HTTPException`: `"wrong login or password"` (through `_unsigned`) ``.
- An exception caught around a raise or a call isn't said, unless the handler raises it again.
- A class says what its validators raise, in a `ValidationError`, and what `__post_init__` raises.

## Findings

"Finds:" follows "Raises:", and is walked the same way (`src/chatddx/stamp/trace.py:Trace`): each
`chatddx.factors.base.Finding` the function makes and its private helpers make, in the order the code reaches them, each
once, as `code`: message, with the message's arguments as a raise's. A computed code or level is `{expr}`; the level is
said when it isn't a warning, ``(`info`, through `_pair`)``. Every code the solidified packages make is in one surface
or another, by name or as the expression that computes it.

Not said:

- What a public function or class it calls raises: its own entry says.
- What is raised without a `raise`: a `KeyError` from a subscript, pydantic's own validation, a library's errors.
- What a function nested in another raises or finds: the walk doesn't enter it.

What isn't said is said with an explicit `raise`, or in a docstring (AGENTS.md, "4. When and how to write a docstring").
