# `chatddx.stamp`

Written by `chatddx stamp write` from `src/chatddx/stamp/`; how to read it is in [docs/surfaces.md](../surfaces.md).

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
* `node: ast.AST`
* ∟`str`

## `Code.source`
`src/chatddx/stamp/code.py:Code.source`

* `obj: griffe.Object`
* `node: ast.AST`
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

## `decorated`
`src/chatddx/stamp/code.py:decorated`

* `node: Node`
* `names: frozenset[str]`
* ∟`bool`

## `Def`
`src/chatddx/stamp/code.py:Def`

`type Def = ast.FunctionDef | ast.AsyncFunctionDef`

## `DOCS`
`src/chatddx/stamp/__init__.py:DOCS`

`DOCS = settings.PROJECT_ROOT / "docs" / "surfaces"`

## `Found` `@dataclass(frozen=True)`
`src/chatddx/stamp/trace.py:Found`

* `code: str`
* `message: str | None`
* `level: str | None = None`
* `through: str | None = None`
* `origin: str | None = None`

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

## `private`
`src/chatddx/stamp/code.py:private`

* `name: str`
* ∟`bool`

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

## `stamped`
`src/chatddx/stamp/markers.py:stamped`

* `current: str | None`
* `written: str`
* ∟`str`

## `stamps`
`src/chatddx/stamp/markers.py:stamps`

* `text: str`
* ∟`list[tuple[str, ...]]`

## `Surface` `@dataclass(frozen=True)`
`src/chatddx/stamp/__init__.py:Surface`

* `path: Path`
* `current: str | None`
* `written: str`

## `Surface.behind` `@property`
`src/chatddx/stamp/__init__.py:Surface.behind`

* ∟`bool`

## `Surface.new` `@property`
`src/chatddx/stamp/__init__.py:Surface.new`

* ∟`int`

## `Surface.pending` `@property`
`src/chatddx/stamp/__init__.py:Surface.pending`

* ∟`int`

## `surfaces`
`src/chatddx/stamp/__init__.py:surfaces`

* `packages: Iterable[str]`
* ∟`list[Surface]`

Raises:
1. `ValueError`: `"{_shown(path)}: {e}"` (from `ValueError`)

## `Trace`
`src/chatddx/stamp/trace.py:Trace`

* `code: Code`
* `finding: str`

## `Trace.__init__`
`src/chatddx/stamp/trace.py:Trace.__init__`

* `code: Code`
* `finding: str`

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

## `write`
`src/chatddx/stamp/__init__.py:write`

* `packages: Sequence[str]`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp write: {e}"` (from `ValueError`)
