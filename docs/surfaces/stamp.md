# `chatddx.stamp`

Written by `chatddx stamp write` from `src/chatddx/stamp/`; how to read it is in [docs/surfaces.md](../surfaces.md).

<<<<<<< signed
## `CLOSING`
`src/chatddx/stamp/markers.py:CLOSING`
=======
## `check`
`src/chatddx/stamp/__init__.py:check`
>>>>>>> @stamp

<<<<<<< signed
`CLOSING = ">>>>>>> @stamp"`
=======
* `packages: Sequence[str]`
* `baseline: bool`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp: {shown} behind the code: run chatddx stamp write"`
2. `SystemExit`: `1`
>>>>>>> @stamp

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

<<<<<<< signed
## `CONFLICT`
`src/chatddx/stamp/markers.py:CONFLICT`

`CONFLICT = ("<<<<<<<", ">>>>>>>")`

## `CONVERSIONS`
`src/chatddx/stamp/trace.py:CONVERSIONS`

`CONVERSIONS = {ord("r"): "!r", ord("s"): "!s", ord("a"): "!a"}`

=======
>>>>>>> @stamp
## `decorated`
`src/chatddx/stamp/code.py:decorated`

* `node: Node`
* `names: frozenset[str]`
* ∟`bool`

## `Def`
`src/chatddx/stamp/code.py:Def`

`type Def = ast.FunctionDef | ast.AsyncFunctionDef`

<<<<<<< signed
## `DIVIDER`
`src/chatddx/stamp/markers.py:DIVIDER`

`DIVIDER = "======="`

=======
>>>>>>> @stamp
## `DOCS`
`src/chatddx/stamp/__init__.py:DOCS`

`DOCS = settings.PROJECT_ROOT / "docs" / "surfaces"`
<<<<<<< signed

## `FINDING`
`src/chatddx/stamp/__init__.py:FINDING`

`FINDING = "chatddx.factors.base.Finding"`
=======
>>>>>>> @stamp

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

<<<<<<< signed
## `OPENING`
`src/chatddx/stamp/markers.py:OPENING`

`OPENING = "<<<<<<< signed"`

## `Page`
`src/chatddx/stamp/page.py:Page`

* `code: Code`
* `trace: Trace`
* `package: griffe.Module`
* `repo: Path`
* `bound: dict[str, tuple[griffe.Class, str]]`

=======
>>>>>>> @stamp
## `page`
`src/chatddx/stamp/page.py:page`

* `code: Code`
* `trace: Trace`
* `package: str`
* `repo: Path`
* ∟`str`
<<<<<<< signed

## `Page.__init__`
`src/chatddx/stamp/page.py:Page.__init__`

* `code: Code`
* `trace: Trace`
* `package: str`
* `repo: Path`

## `Page.annotated`
`src/chatddx/stamp/page.py:Page.annotated`

* `obj: griffe.Object`
* `valued: bool`
* ∟`str`

## `Page.binds`
`src/chatddx/stamp/page.py:Page.binds`

* `cls: griffe.Class`
* ∟`dict[str, griffe.Function]`

## `Page.cls`
`src/chatddx/stamp/page.py:Page.cls`

* `cls: griffe.Class`
* `prefix: str`
* ∟`list[tuple[str, list[str]]]`

## `Page.decorator`
`src/chatddx/stamp/page.py:Page.decorator`

* `obj: griffe.Object`
* `node: ast.expr`
* ∟`str`

## `Page.entry`
`src/chatddx/stamp/page.py:Page.entry`

* `member: griffe.Object`
* `prefix: str`
* ∟`list[tuple[str, list[str]]]`

## `Page.finds`
`src/chatddx/stamp/page.py:Page.finds`

* `found: tuple[Found, ...]`
* ∟`list[str]`

## `Page.function`
`src/chatddx/stamp/page.py:Page.function`

* `function: griffe.Object`
* `name: str`
* `cls: griffe.Class | None`
* `drop: int`
* ∟`list[str]`

## `Page.heading`
`src/chatddx/stamp/page.py:Page.heading`

* `name: str`
* `obj: griffe.Object`
* `node: Node | None = None`
* ∟`list[str]`

## `Page.listed`
`src/chatddx/stamp/page.py:Page.listed`

* `raised: tuple[Raised, ...]`
* ∟`list[str]`

## `Page.modules`
`src/chatddx/stamp/page.py:Page.modules`

* `module: griffe.Module`
* ∟`list[griffe.Module]`

## `Page.noted`
`src/chatddx/stamp/page.py:Page.noted`

* `f: Found`
* ∟`str`

## `Page.parameters`
`src/chatddx/stamp/page.py:Page.parameters`

* `function: griffe.Object`
* `node: Def`
* `drop: int`
* ∟`list[str]`

## `Page.render`
`src/chatddx/stamp/page.py:Page.render`

* ∟`str`

## `Page.said`
`src/chatddx/stamp/page.py:Page.said`

* `r: Raised`
* ∟`str`

## `Page.written`
`src/chatddx/stamp/page.py:Page.written`

* `obj: griffe.Object`
* ∟`list[str]`

## `pending`
`src/chatddx/stamp/markers.py:pending`

* `text: str`
* ∟`int`
=======
>>>>>>> @stamp

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

<<<<<<< signed
## `regenerated`
`src/chatddx/stamp/__init__.py:regenerated`

* `packages: Iterable[str]`
* ∟`dict[Path, str]`

=======
>>>>>>> @stamp
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
<<<<<<< signed
=======

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
>>>>>>> @stamp

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

<<<<<<< signed
## `VALIDATION`
`src/chatddx/stamp/trace.py:VALIDATION`

`VALIDATION = "pydantic.ValidationError"`

=======
>>>>>>> @stamp
## `VALIDATORS`
`src/chatddx/stamp/trace.py:VALIDATORS`

`VALIDATORS = frozenset(…)`
<<<<<<< signed
=======

## `write`
`src/chatddx/stamp/__init__.py:write`

* `packages: Sequence[str]`
* ∟`None`

Raises:
1. `SystemExit`: `"stamp write: {e}"` (from `ValueError`)
>>>>>>> @stamp
