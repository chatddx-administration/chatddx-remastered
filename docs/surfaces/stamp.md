# `chatddx.stamp`

Written by `chatddx stamp write` from `src/chatddx/stamp/`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

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
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `check`
`src/chatddx/stamp/__init__.py:check`

* `packages: Sequence[str]`
* `baseline: bool`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp: {shown} behind the code: run chatddx stamp write"`
2. `SystemExit`: `1`

## `Code`
`src/chatddx/stamp/code.py:Code`

* `src: Path`
* `root: griffe.Module`

## `Code.__init__`
`src/chatddx/stamp/code.py:Code.__init__`

* `src: Path`
* `package: str`

## `Code.bases`
`src/chatddx/stamp/code.py:Code.bases`

* `cls: griffe.Class`
* ∟`list[str]`

## `Code.file`
`src/chatddx/stamp/code.py:Code.file`

* `path: Path`
* ∟`File`

## `Code.get`
`src/chatddx/stamp/code.py:Code.get`

* `path: str`
* ∟`griffe.Object | None`

## `Code.handled`
`src/chatddx/stamp/code.py:Code.handled`

* `module: griffe.Module`
* `expr: ast.expr`
* ∟`list[str]`

## `Code.lines`
`src/chatddx/stamp/code.py:Code.lines`

* `obj: griffe.Object`
* ∟`list[str]`

## `Code.lookup`
`src/chatddx/stamp/code.py:Code.lookup`

* `module: griffe.Module`
* `expr: ast.expr`
* ∟`str | None`

## `Code.member`
`src/chatddx/stamp/code.py:Code.member`

* `cls: griffe.Class`
* `name: str`
* ∟`griffe.Object | None`

## `Code.named`
`src/chatddx/stamp/code.py:Code.named`

* `expr: griffe.ExprName`
* ∟`str`

## `Code.node`
`src/chatddx/stamp/code.py:Code.node`

* `obj: griffe.Object`
* ∟`Node`

## `Code.segment`
`src/chatddx/stamp/code.py:Code.segment`

* `obj: griffe.Object`
* `node: Spanned`
* ∟`str`

## `Code.source`
`src/chatddx/stamp/code.py:Code.source`

* `obj: griffe.Object`
* `node: Spanned`
* ∟`str | None`

## `Code.subclass`
`src/chatddx/stamp/code.py:Code.subclass`

* `path: str`
* `of: str`
* ∟`bool`

## `Code.text`
`src/chatddx/stamp/code.py:Code.text`

* `module: griffe.Module`
* `expr: ast.expr`
* ∟`str | None`

## `COMMENTS`
`src/chatddx/stamp/__init__.py:COMMENTS`

`COMMENTS = settings.PROJECT_ROOT / "docs" / "comments"`

## `decorated`
`src/chatddx/stamp/code.py:decorated`

* `node: Node`
* `names: frozenset[str]`
* ∟`bool`

## `Def`
`src/chatddx/stamp/code.py:Def`

`type Def = ast.FunctionDef | ast.AsyncFunctionDef`

## `File` `@dataclass(frozen=True)`
`src/chatddx/stamp/code.py:File`

* `source: str`
* `tree: ast.Module`

## `File.lines` `@cached_property`
`src/chatddx/stamp/code.py:File.lines`

* ∟`list[str]`

## `File.names` `@cached_property`
`src/chatddx/stamp/code.py:File.names`

* ∟`list[tuple[str, int, int, int]]`

## `File.nodes` `@cached_property`
`src/chatddx/stamp/code.py:File.nodes`

* ∟`dict[int, Node]`

## `File.segment`
`src/chatddx/stamp/code.py:File.segment`

* `node: Spanned`
* `padded: bool = False`
* ∟`str | None`

## `Found` `@dataclass(frozen=True)`
`src/chatddx/stamp/trace.py:Found`

* `code: str`
* `message: str | None`
* `level: str | None = None`
* `through: str | None = None`
* `origin: str | None = None`

## `index`
`src/chatddx/stamp/index.py:index`

* `code: Code`
* `package: str`
* `repo: Path`
* ∟`str`

## `Node`
`src/chatddx/stamp/code.py:Node`

`type Node = Def | ast.ClassDef`

## `page`
`src/chatddx/stamp/page.py:page`

* `code: Code`
* `trace: Trace`
* `package: str`
* `repo: Path`
* ∟`str`

## `PENDING`
`src/chatddx/stamp/markers.py:PENDING`

`PENDING = …`

## `private`
`src/chatddx/stamp/code.py:private`

* `name: str`
* ∟`bool`

## `Proof` `@dataclass(frozen=True)`
`src/chatddx/stamp/__init__.py:Proof`

* `path: Path`
* `current: str | None`
* `written: str`

## `Proof.behind` `@property`
`src/chatddx/stamp/__init__.py:Proof.behind`

* ∟`bool`

## `Proof.new` `@property`
`src/chatddx/stamp/__init__.py:Proof.new`

* ∟`int`

## `Proof.pending` `@property`
`src/chatddx/stamp/__init__.py:Proof.pending`

* ∟`int`

## `proofs`
`src/chatddx/stamp/__init__.py:proofs`

* `packages: Iterable[str]`
* ∟`list[Proof]`

Raises:
1. `ValueError`: `"{_shown(path)}: {e}"` (from `ValueError`)

## `Raised` `@dataclass(frozen=True)`
`src/chatddx/stamp/trace.py:Raised`

* `exception: str`
* `message: str | None`
* `kind: str | None`
* `through: str | None = None`
* `validated: bool = False`
* `origin: str | None = None`

## `signed`
`src/chatddx/stamp/markers.py:signed`

* `text: str`
* ∟`list[str]`

Raises:
1. `ValueError`: `"line {n}: a conflict marker that isn't a stamp's"`
2. `ValueError`: `"line {opened}: a stamp isn't closed"`

## `Spanned`
`src/chatddx/stamp/code.py:Spanned`

`type Spanned = ast.expr | ast.stmt | ast.type_param`

## `stamped`
`src/chatddx/stamp/markers.py:stamped`

* `current: str | None`
* `written: str`
* ∟`str`

## `stamps`
`src/chatddx/stamp/markers.py:stamps`

* `text: str`
* ∟`list[tuple[str, ...]]`

## `SURFACES`
`src/chatddx/stamp/__init__.py:SURFACES`

`SURFACES = settings.PROJECT_ROOT / "docs" / "surfaces"`

## `Trace`
`src/chatddx/stamp/trace.py:Trace`

* `code: Code`
* `findings: tuple[str, str]`
* `whoops: str`

## `Trace.__init__`
`src/chatddx/stamp/trace.py:Trace.__init__`

* `code: Code`
* `finding: str`
* `whoops: str`

## `Trace.caught`
`src/chatddx/stamp/trace.py:Trace.caught`

* `kind: str | None`
* `caught: tuple[str, ...]`
* ∟`bool`

## `Trace.constructing`
`src/chatddx/stamp/trace.py:Trace.constructing`

* `cls: griffe.Class`
* ∟`tuple[Raised, ...]`

## `Trace.of`
`src/chatddx/stamp/trace.py:Trace.of`

* `function: griffe.Object`
* `cls: griffe.Class | None`
* ∟`Traced`

## `Traced` `@dataclass(frozen=True)`
`src/chatddx/stamp/trace.py:Traced`

* `raised: tuple[Raised, ...]`
* `found: tuple[Found, ...]`

## `VALIDATORS`
`src/chatddx/stamp/trace.py:VALIDATORS`

`VALIDATORS = frozenset(…)`

## `WHOOPSES`
`src/chatddx/stamp/__init__.py:WHOOPSES`

`WHOOPSES = settings.PROJECT_ROOT / "docs" / "whoopses"`

## `whoopses`
`src/chatddx/stamp/index.py:whoopses`

* `code: Code`
* `package: str`
* `repo: Path`
* `whoops: str`
* ∟`str`

## `write`
`src/chatddx/stamp/__init__.py:write`

* `packages: Sequence[str]`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp write: {e}"` (from `ValueError`)
