# Reading a surface

Each file in docs/surfaces/* is written by `chatddx stamp` from a package of `settings.STAMPED`: an entry for each
public name, sorted alphabetically whatever its case, so that a class's members follow it. An entry's heading is the
name, with its decorators, type parameters and bases; below it is where the code is.

- The bullets are a function's parameters or a class's fields, and `∟` the return type, which a class and its `__init__`
  leave out: calling a class gives one of it. A constant or a type alias is its definition, without a bullet. `*`: the
  parameters after it are keyword-only; `/`: those before it are positional-only. A function a class binds as an
  attribute is its method: its first parameter, the instance, is left out.
- Raises: the function's own `raise` statements and its private helpers' (through `<helper>`), in the order the code
  reaches them, each once. What the public functions it calls raise is in their own entries.
- A message is in code: text quoted, with the values of the code that raises it as `{expr}`, and an argument that isn't
  text as written; from `<exception>` when it is the exception caught.
- Finds: each `Finding` the function makes, as `code`: message, followed as Raises are; a warning unless it says another
  level, such as `info`.
- A change in the code waits for a stamp as a git conflict: the lines between `<<<<<<< signed` and `=======` are as last
  stamped, and those between `=======` and `>>>>>>> @stamp` are what the code says now. Keeping the latter, and taking
  the rest away, as a conflict tool's "theirs" does, is the stamp.
