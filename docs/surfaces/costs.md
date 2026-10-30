# `costs`

Written by `chatddx-dev index` from `[parts.costs]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

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

## `command`
`dev/src/chatddx_dev/costs/__init__.py:command`

The command pytest ran as, its plugins named by -p and its verbosity left out.

* `args: Sequence[str]`
* ∟`str`

## `Cost` `@dataclass(frozen=True)`
`dev/src/chatddx_dev/costs/__init__.py:Cost`

* `when: str`
* `machine: str`
* `seconds: float`
* `status: int`
* `beside: int`
* `commit: str`
* `command: str`

## `Cost.read` `@classmethod`
`dev/src/chatddx_dev/costs/__init__.py:Cost.read`

* `line: str`
* ∟`"Cost"`

## `Cost.written`
`dev/src/chatddx_dev/costs/__init__.py:Cost.written`

* ∟`str`

## `Costs`
`dev/src/chatddx_dev/costs/__init__.py:Costs`

* `command: str`
* `began: float`
* `status: int | None`

## `Costs.__init__`
`dev/src/chatddx_dev/costs/__init__.py:Costs.__init__`

* `args: Sequence[str]`

## `Costs.pytest_sessionfinish`
`dev/src/chatddx_dev/costs/__init__.py:Costs.pytest_sessionfinish`

* `exitstatus: int`
* ∟`None`

## `Costs.pytest_unconfigure`
`dev/src/chatddx_dev/costs/__init__.py:Costs.pytest_unconfigure`

* ∟`None`

## `LOG`
`dev/src/chatddx_dev/costs/__init__.py:LOG`

`LOG = project.PROJECT_ROOT / "dev" / "costs.tsv"`

## `logged`
`dev/src/chatddx_dev/costs/__init__.py:logged`

Appends a line to the spool, if in a checkout, as told by the log being there.

* `cost: Cost`
* `spool: Path = SPOOL`
* `log: Path = LOG`
* ∟`None`

## `MARGIN`
`dev/src/chatddx_dev/costs/__init__.py:MARGIN`

`MARGIN = 1.5`

## `medians`
`dev/src/chatddx_dev/costs/__init__.py:medians`

Each command's median over its RECENT latest passes on the machine, run alone.

* `costs: Iterable[Cost]`
* `machine: str`
* ∟`dict[str, float]`

## `pytest_configure`
`dev/src/chatddx_dev/costs/__init__.py:pytest_configure`

* `config: pytest.Config`
* ∟`None`

## `quoted`
`dev/src/chatddx_dev/costs/__init__.py:quoted`

The text, its figures that are off by more than MARGIN made the median.

A figure is a ~<n>s in a list item whose first code span is the command, and only
what a stamp pending holds as written now is read.

* `text: str`
* `took: dict[str, float]`
* ∟`str`

## `QUOTED_IN`
`dev/src/chatddx_dev/costs/__init__.py:QUOTED_IN`

`QUOTED_IN = tuple(project.PROJECT_ROOT / path for path in project.COSTS_QUOTED_IN)`

## `read`
`dev/src/chatddx_dev/costs/__init__.py:read`

* `*paths: Path`
* ∟`list[Cost]`

## `RECENT`
`dev/src/chatddx_dev/costs/__init__.py:RECENT`

`RECENT = 5`

## `show`
`dev/src/chatddx_dev/costs/__init__.py:show`

Prints each command's median per machine, as write would quote it.

* `spool: Path = SPOOL`
* `log: Path = LOG`
* ∟`None`

## `SPOOL`
`dev/src/chatddx_dev/costs/__init__.py:SPOOL`

`SPOOL = project.PROJECT_ROOT / "dev" / "state" / "costs-spool.tsv"`

## `write`
`dev/src/chatddx_dev/costs/__init__.py:write`

Folds the spool into the log, and rewrites the figures quoted off the log.

The figures are those of project.COSTS_QUOTED's machine; it says what it wrote.

* `spool: Path = SPOOL`
* `log: Path = LOG`
* `quoted_in: Sequence[Path] = QUOTED_IN`
* ∟`None`
