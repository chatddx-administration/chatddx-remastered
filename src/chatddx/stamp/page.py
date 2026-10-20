import ast
import re
from collections import Counter
from pathlib import Path

import griffe

from .code import Code, Def, Node, decorated, private
from .trace import VALIDATORS, Found, Raised, Trace

LEGEND = """\
# Reading a reference

Each file here is written by `chatddx stamp` from a package of `settings.STAMPED`: an entry for each public name,
sorted alphabetically whatever its case, so that a class's members follow it. An entry's heading is the name, with its
decorators, type parameters and bases; below it is where the code is.

- The bullets are a function's parameters or a class's fields, and `∟` the return type, which a class and its
  `__init__` leave out: calling a class gives one of it. A constant or a type alias is its definition, without a bullet.
  `*`: the parameters after it are keyword-only; `/`: those before it are positional-only. A function a class binds as
  an attribute is its method: its first parameter, the instance, is left out.
- Raises: the function's own `raise` statements and its private helpers' (through `<helper>`), in the order the code
  reaches them, each once. What the public functions it calls raise is in their own entries.
- A message is in code: text quoted, with the values of the code that raises it as `{expr}`, and an argument that
  isn't text as written; from `<exception>` when it is the exception caught.
- Finds: each `Finding` the function makes, as `code`: message, followed as Raises are; a warning unless it says
  another level, such as `info`.
- A change in the code waits for a stamp as a git conflict: the lines between `<<<<<<< signed` and `=======` are as
  last stamped, and those between `=======` and `>>>>>>> @stamp` are what the code says now. Keeping the latter, and
  taking the rest away, as a conflict tool's "theirs" does, is the stamp.
"""


def _head(value: str | griffe.Expr) -> str:
    if isinstance(value, str):
        return value if len(value) <= 60 else "…"
    if isinstance(value, griffe.ExprCall):
        return f"{value.function}(…)"
    if isinstance(value, griffe.ExprSubscript):
        return f"{value.left}[…]"
    for kind, written in (
        (griffe.ExprDict, "{…}"),
        (griffe.ExprSet, "{…}"),
        (griffe.ExprList, "[…]"),
        (griffe.ExprTuple, "(…)"),
    ):
        if isinstance(value, kind):
            return written
    return "…"


def _noted(name: str, message: str | None, notes: list[str]) -> str:
    written = _code(name) + ("" if message is None else f": {_code(message)}")
    return written + (f" ({', '.join(notes)})" if notes else "")


def _code(text: str) -> str:
    if "`" not in text:
        return f"`{text}`"
    fence = "`" * (max(len(run) for run in re.findall("`+", text)) + 1)
    return f"{fence} {text} {fence}"


class Page:
    def __init__(self, code: Code, trace: Trace, package: str, repo: Path) -> None:
        found = code.get(package)
        assert isinstance(found, griffe.Module)
        self.code: Code = code
        self.trace: Trace = trace
        self.package: griffe.Module = found
        self.repo: Path = repo
        self.bound: dict[str, tuple[griffe.Class, str]] = {}
        for module in self.modules(found):
            for cls in module.classes.values():
                for name, function in self.binds(cls).items():
                    self.bound[function.path] = (cls, name)

    def modules(self, module: griffe.Module) -> list[griffe.Module]:
        found = [module]
        for name, sub in module.modules.items():
            if name != "test" and not private(name):
                found += self.modules(sub)
        return found

    def binds(self, cls: griffe.Class) -> dict[str, griffe.Function]:
        found: dict[str, griffe.Function] = {}
        for name, member in cls.members.items():
            if isinstance(member, griffe.Attribute) and isinstance(
                member.value, griffe.ExprName
            ):
                held = cls.module.members.get(member.value.name)
                target = held.final_target if isinstance(held, griffe.Alias) else held
                if isinstance(target, griffe.Function):
                    found[name] = target
        return found

    def render(self) -> str:
        named: list[tuple[str, griffe.Object]] = []
        for module in self.modules(self.package):
            for name, member in module.members.items():
                if not (
                    isinstance(member, (griffe.Alias, griffe.Module))
                    or private(name)
                    or name == "__all__"
                    or member.path in self.bound
                ):
                    named.append((name, member))
        counted = Counter(name for name, _ in named)
        entries: list[tuple[str, str, list[str]]] = []
        for name, member in named:
            within = member.module.path.removeprefix(self.package.path).lstrip(".")
            prefix = f"{within or '__init__'}." if counted[name] > 1 else ""
            entries += [(n, prefix, lines) for n, lines in self.entry(member, prefix)]
        entries.sort(key=lambda e: (e[0].casefold(), e[0], e[1]))
        directory = self.code.src.relative_to(self.repo).joinpath(
            *self.package.path.split(".")
        )
        lines = [
            f"# `{self.package.path}`",
            "",
            f"Written by `chatddx stamp` from `{directory}/`; how to read it is in "
            + "[docs/reference/README.md](README.md).",
        ]
        for _, _, written in entries:
            lines += ["", *written]
        return "\n".join(lines) + "\n"

    def entry(self, member: griffe.Object, prefix: str) -> list[tuple[str, list[str]]]:
        if isinstance(member, griffe.Function):
            display = prefix + member.name
            return [(member.name, self.function(member, display, None, drop=0))]
        if isinstance(member, griffe.Class):
            return self.cls(member, prefix)
        if isinstance(member, (griffe.Attribute, griffe.TypeAlias)):
            heading = self.heading(prefix + member.name, member)
            return [(member.name, [*heading, *self.written(member)])]
        return []

    def heading(
        self, name: str, obj: griffe.Object, node: Node | None = None
    ) -> list[str]:
        marks = (
            []
            if node is None
            else [self.decorator(obj, d) for d in node.decorator_list]
        )
        if node is not None and node.type_params:
            marks.append(
                _code(
                    f"[{', '.join(self.code.segment(obj, t) for t in node.type_params)}]"
                )
            )
        if isinstance(node, ast.ClassDef) and node.bases:
            marks.append(
                _code(f"({', '.join(self.code.segment(obj, b) for b in node.bases)})")
            )
        assert isinstance(obj.filepath, Path)
        local = obj.path.removeprefix(f"{obj.module.path}.")
        return [
            " ".join([f"## {_code(name)}", *marks]),
            _code(f"{obj.filepath.relative_to(self.repo)}:{local}"),
        ]

    def decorator(self, obj: griffe.Object, node: ast.expr) -> str:
        written = self.code.source(obj, node)
        if written is not None and "\n" not in written:
            return _code(f"@{written}")
        if not isinstance(node, ast.Call):
            return _code(f"@{self.code.segment(obj, node)}")
        first = [self.code.source(obj, a) for a in node.args[:1]]
        shown = [a for a in first if a is not None and "\n" not in a]
        return _code(
            f"@{self.code.segment(obj, node.func)}({', '.join([*shown, '…'])})"
        )

    def written(self, obj: griffe.Object) -> list[str]:
        lines = self.code.lines(obj)
        if len(lines) == 1:
            return ["", _code(lines[0].strip())]
        return ["", _code(self.annotated(obj, valued=True))]

    def annotated(self, obj: griffe.Object, valued: bool) -> str:
        written = obj.name
        if isinstance(obj, griffe.Attribute) and obj.annotation is not None:
            written += f": {obj.annotation}"
        if valued and isinstance(obj, griffe.Attribute) and obj.value is not None:
            written += f" = {_head(obj.value)}"
        return written

    def function(
        self, function: griffe.Object, name: str, cls: griffe.Class | None, drop: int
    ) -> list[str]:
        node = self.code.node(function)
        assert not isinstance(node, ast.ClassDef)
        lines = self.heading(name, function, node)
        if docstring := ast.get_docstring(node):
            lines += ["", *docstring.splitlines()]
        bullets = self.parameters(function, node, drop)
        if node.returns is not None and node.name != "__init__":
            bullets.append(f"* ∟{_code(self.code.segment(function, node.returns))}")
        if bullets:
            lines += ["", *bullets]
        traced = self.trace.of(function, cls)
        return lines + self.listed(traced.raised) + self.finds(traced.found)

    def parameters(self, function: griffe.Object, node: Def, drop: int) -> list[str]:
        args = node.args

        def one(arg: ast.arg, default: ast.expr | None, mark: str = "") -> str:
            written = mark + arg.arg
            if arg.annotation is not None:
                written += f": {self.code.segment(function, arg.annotation)}"
            if default is not None:
                spaced = " = " if arg.annotation is not None else "="
                written += spaced + self.code.segment(function, default)
            return f"* {_code(written)}"

        positional = [*args.posonlyargs, *args.args]
        defaults: list[ast.expr | None] = [None] * (
            len(positional) - len(args.defaults)
        )
        defaults += args.defaults
        bullets: list[str] = []
        for i, (arg, default) in enumerate(zip(positional, defaults, strict=True)):
            if i >= drop:
                bullets.append(one(arg, default))
            if args.posonlyargs and i == len(args.posonlyargs) - 1 and i >= drop:
                bullets.append("* `/`")
        if args.vararg is not None:
            bullets.append(one(args.vararg, None, "*"))
        elif args.kwonlyargs:
            bullets.append("* `*`")
        bullets += [
            one(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True)
        ]
        if args.kwarg is not None:
            bullets.append(one(args.kwarg, None, "**"))
        return bullets

    def listed(self, raised: tuple[Raised, ...]) -> list[str]:
        if not raised:
            return []
        return [
            "",
            "Raises:",
            *(f"{i}. {self.said(r)}" for i, r in enumerate(raised, 1)),
        ]

    def said(self, r: Raised) -> str:
        notes = [] if r.origin is None else [f"from {_code(r.origin)}"]
        if r.through is not None:
            notes.append(f"through {_code(r.through)}")
        if r.validated:
            notes.append("in a `ValidationError`")
        return _noted(r.exception, r.message, notes)

    def finds(self, found: tuple[Found, ...]) -> list[str]:
        if not found:
            return []
        return [
            "",
            "Finds:",
            *(f"{i}. {self.noted(f)}" for i, f in enumerate(found, 1)),
        ]

    def noted(self, f: Found) -> str:
        notes = [] if f.level is None else [_code(f.level)]
        if f.origin is not None:
            notes.append(f"from {_code(f.origin)}")
        if f.through is not None:
            notes.append(f"through {_code(f.through)}")
        return _noted(f.code, f.message, notes)

    def cls(self, cls: griffe.Class, prefix: str) -> list[tuple[str, list[str]]]:
        node = self.code.node(cls)
        lines = self.heading(prefix + cls.name, cls, node)
        if docstring := ast.get_docstring(node):
            lines += ["", *docstring.splitlines()]
        binds = self.binds(cls)
        methods = [
            (r.lineno, r.endlineno or r.lineno)
            for r in cls.members.values()
            if isinstance(r, griffe.Function) and r.lineno
        ]
        fields: list[str] = []
        entries: list[tuple[str, list[str]]] = []
        for name, member in cls.members.items():
            if isinstance(member, griffe.Alias) or (
                private(name) and name not in binds
            ):
                continue
            display = f"{prefix}{cls.name}.{name}"
            if name in binds:
                entries.append(
                    (display, self.function(binds[name], display, cls, drop=1))
                )
            elif isinstance(member, griffe.Attribute) and "property" in member.labels:
                entries.append((display, self.function(member, display, cls, drop=1)))
            elif isinstance(member, griffe.Attribute) and member.lineno:
                within = any(a <= member.lineno <= b for a, b in methods)
                text = (
                    self.code.lines(member)[0].strip()
                    if member.lineno == member.endlineno
                    else ""
                )
                if within or not text:
                    text = self.annotated(member, valued=not within)
                fields.append(f"* {_code(text)}")
            elif isinstance(member, griffe.Function) and member.lineno:
                held = self.code.node(member)
                if decorated(held, VALIDATORS) or name == "__post_init__":
                    continue
                static = decorated(held, frozenset({"staticmethod"}))
                entries.append(
                    (
                        display,
                        self.function(member, display, cls, drop=0 if static else 1),
                    )
                )
        if fields:
            lines += ["", *fields]
        lines += self.listed(self.trace.constructing(cls))
        return [(cls.name, lines), *((d.removeprefix(prefix), e) for d, e in entries)]


def page(code: Code, trace: Trace, package: str, repo: Path) -> str:
    return Page(code, trace, package, repo).render()
