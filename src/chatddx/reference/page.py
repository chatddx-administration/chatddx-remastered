import ast
from pathlib import Path

import griffe

from .code import Code, Def, Node, decorated, private
from .raises import VALIDATORS, Raised, Raises


def _code(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


class Page:
    def __init__(self, code: Code, raises: Raises, package: str, repo: Path) -> None:
        found = code.get(package)
        assert isinstance(found, griffe.Module)
        self.code: Code = code
        self.raises: Raises = raises
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
        entries: list[tuple[str, list[str]]] = []
        for module in self.modules(self.package):
            for name, member in module.members.items():
                if (
                    isinstance(member, griffe.Alias)
                    or private(name)
                    or name == "__all__"
                ):
                    continue
                entries += self.entry(member)
        entries.sort(key=lambda e: (e[0].casefold(), e[0]))
        directory = self.code.src.relative_to(self.repo).joinpath(
            *self.package.path.split(".")
        )
        lines = [
            f"# `{self.package.path}`",
            "",
            f"Written by `chatddx reference` from `{directory}/`: each public name's signature "
            + "and what it raises, in the order the code raises it.",
        ]
        for _, written in entries:
            lines += ["", *written]
        return "\n".join(lines) + "\n"

    def entry(self, member: griffe.Object) -> list[tuple[str, list[str]]]:
        if isinstance(member, griffe.Function):
            if member.path in self.bound:
                return []
            return [(member.name, self.function(member, member.name, None, drop=0))]
        if isinstance(member, griffe.Class):
            return self.cls(member)
        if isinstance(member, (griffe.Attribute, griffe.TypeAlias)):
            return [
                (
                    member.name,
                    [*self.heading(member.name, member), *self.written(member)],
                )
            ]
        return []

    def heading(
        self, name: str, obj: griffe.Object, node: Node | None = None
    ) -> list[str]:
        marks = (
            []
            if node is None
            else [f"`@{self.code.segment(obj, d)}`" for d in node.decorator_list]
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
            " ".join([f"## {name}", *marks]),
            _code(f"{obj.filepath.relative_to(self.repo)}:{local}"),
        ]

    def written(self, obj: griffe.Object) -> list[str]:
        lines = self.code.lines(obj)
        if len(lines) == 1:
            return ["", f"* {_code(lines[0].strip())}"]
        return ["", f"* {_code(self.annotated(obj))}"]

    def annotated(self, obj: griffe.Object) -> str:
        if isinstance(obj, griffe.Attribute) and obj.annotation is not None:
            return f"{obj.name}: {obj.annotation}"
        return obj.name

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
        return lines + self.listed(self.raises.of(function, cls))

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
            "",
            *(f"{i}. {self.said(r)}" for i, r in enumerate(raised, 1)),
        ]

    def said(self, r: Raised) -> str:
        written = _code(r.exception) + ("" if r.message is None else f": {r.message}")
        notes = [] if r.through is None else [f"through {_code(r.through)}"]
        if r.validated:
            notes.append("in a `ValidationError`")
        return written + (f" ({', '.join(notes)})" if notes else "")

    def cls(self, cls: griffe.Class) -> list[tuple[str, list[str]]]:
        node = self.code.node(cls)
        lines = self.heading(cls.name, cls, node)
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
            display = f"{cls.name}.{name}"
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
                    text = self.annotated(member)
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
        lines += self.listed(self.raises.constructing(cls))
        return [(cls.name, lines), *entries]


def page(code: Code, raises: Raises, package: str, repo: Path) -> str:
    return Page(code, raises, package, repo).render()
