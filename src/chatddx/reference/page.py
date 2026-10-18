import ast
import inspect
from collections.abc import Collection

from .index import VALIDATORS, Class, Def, Function, Index, Module, decorated
from .raises import Raised, Raises, private

PROPERTIES = frozenset({"property", "cached_property"})


def code(text: str) -> str:
    return f"`` {text} ``" if "`" in text else f"`{text}`"


class Page:
    def __init__(self, index: Index, raises: Raises, package: str) -> None:
        self.index: Index = index
        self.raises: Raises = raises
        self.package: str = package
        self.bound: dict[str, str] = {}
        for q, c in index.classes.items():
            if self.ours(c.module):
                for attr, function in index.bound(q).items():
                    self.bound[function] = f"{c.name}.{attr}"

    def ours(self, module: Module) -> bool:
        inside = module.name == self.package or module.name.startswith(
            f"{self.package}."
        )
        return inside and not private(module.name)

    def name(self, q: str) -> str:
        if q in self.bound:
            return self.bound[q]
        owner = self.index.owner(q)
        if owner is None:
            return q.removeprefix("builtins.")
        local = q.removeprefix(f"{owner}.")
        if owner == self.package or owner.startswith(f"{self.package}."):
            return local
        project = self.package.split(".")[0]
        package = ".".join(owner.split(".")[:2])
        exported = self.index.modules.get(package)
        top = local.split(".")[0]
        if (
            exported is not None
            and top in exported.imports
            and self.index.canonical(exported.imports[top]) == f"{owner}.{top}"
        ):
            owner = package
        return f"{owner}.{local}".removeprefix(f"{project}.")

    def render(self) -> str:
        entries: list[tuple[str, list[str]]] = []
        for module in self.index.modules.values():
            if not self.ours(module):
                continue
            for node in module.tree.body:
                entries += self.entry(module, node)
        entries.sort(key=lambda e: (e[0].casefold(), e[0]))
        root = self.index.root.name
        directory = f"{root}/{self.package.replace('.', '/')}/"
        lines = [
            f"# {code(self.package)}",
            "",
            f"Written by `chatddx reference` from `{directory}`: each public name's signature and what it "
            + "raises.",
        ]
        for _, written in entries:
            lines += ["", *written]
        return "\n".join(lines) + "\n"

    def entry(self, module: Module, node: ast.stmt) -> list[tuple[str, list[str]]]:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            q = f"{module.name}.{node.name}"
            if private(node.name) or q in self.bound:
                return []
            heading = self.signature(module, node, node.name, drop=0)
            return [
                (node.name, [f"## {code(heading)}", self.path(q), *self.about(q, node)])
            ]
        if isinstance(node, ast.ClassDef):
            return (
                []
                if private(node.name)
                else [(node.name, self.cls(f"{module.name}.{node.name}"))]
            )
        if isinstance(node, ast.TypeAlias):
            name = node.name.id
            q = f"{module.name}.{name}"
            return (
                []
                if private(name)
                else [(name, [f"## {code(module.segment(node))}", self.path(q)])]
            )
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if len(names) != 1 or private(names[0]) or names[0] == "__all__":
                return []
            q = f"{module.name}.{names[0]}"
            return [
                (
                    names[0],
                    [f"## {code(self.constant(module, node, names[0]))}", self.path(q)],
                )
            ]
        return []

    def path(self, q: str) -> str:
        owner = self.index.owner(q)
        assert owner is not None
        module = self.index.modules[owner]
        root = self.index.root.parent
        return code(f"{module.path.relative_to(root)}:{q.removeprefix(f'{owner}.')}")

    def constant(
        self, module: Module, node: ast.Assign | ast.AnnAssign, name: str
    ) -> str:
        written = name
        if isinstance(node, ast.AnnAssign):
            written += f": {module.segment(node.annotation)}"
        if node.value is not None:
            value = ast.get_source_segment(module.source, node.value)
            if value is not None and "\n" not in value:
                written += f" = {value}"
        return written

    def signature(self, module: Module, node: Def, name: str, drop: int) -> str:
        decorators = [f"@{module.segment(d)} " for d in node.decorator_list]
        params = (
            f"[{', '.join(module.segment(t) for t in node.type_params)}]"
            if node.type_params
            else ""
        )
        returns = (
            f" -> {module.segment(node.returns)}"
            if node.returns and node.name != "__init__"
            else ""
        )
        kind = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        return f"{''.join(decorators)}{kind}{name}{params}({self.arguments(module, node.args, drop)}){returns}"

    def arguments(self, module: Module, args: ast.arguments, drop: int) -> str:
        def one(arg: ast.arg, default: ast.expr | None) -> str:
            written = arg.arg
            if arg.annotation is not None:
                written += f": {module.segment(arg.annotation)}"
                if default is not None:
                    written += f" = {module.segment(default)}"
            elif default is not None:
                written += f"={module.segment(default)}"
            return written

        positional = [*args.posonlyargs, *args.args]
        defaults: list[ast.expr | None] = [None] * (
            len(positional) - len(args.defaults)
        )
        defaults += args.defaults
        written: list[str] = []
        for i, (arg, default) in enumerate(zip(positional, defaults, strict=True)):
            if i >= drop:
                written.append(one(arg, default))
            if args.posonlyargs and i == len(args.posonlyargs) - 1 and i >= drop:
                written.append("/")
        if args.vararg is not None:
            written.append("*" + one(args.vararg, None))
        elif args.kwonlyargs:
            written.append("*")
        written += [
            one(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True)
        ]
        if args.kwarg is not None:
            written.append("**" + one(args.kwarg, None))
        return ", ".join(written)

    def about(self, q: str, node: Def) -> list[str]:
        return [*self.docstring(node), *self.raised_by(q)]

    def docstring(self, node: Def | ast.ClassDef) -> list[str]:
        docstring = ast.get_docstring(node)
        return inspect.cleandoc(docstring).splitlines() if docstring else []

    def raised_by(self, q: str, skip: Collection[str] = ()) -> list[str]:
        lines: list[str] = []
        shown = self.raises.shown(q)
        lines += [f"- raises {self.raised(r)}" for r in shown.raised]
        via = sorted({self.name(v) for v in shown.via if v not in skip})
        if via:
            listed = ", ".join(code(v) for v in via)
            lines.append(
                f"- raises what {listed} {'raises' if len(via) == 1 else 'raise'}"
            )
        return lines

    def raised(self, r: Raised) -> str:
        written = self.name(r.exception) + ("" if r.said is None else f"({r.said})")
        return (
            f"{code(written)} in a `ValidationError`" if r.validated else code(written)
        )

    def cls(self, q: str) -> list[str]:
        c: Class = self.index.classes[q]
        module, node = c.module, c.node
        decorators = "".join(f"@{module.segment(d)} " for d in node.decorator_list)
        bases = [module.segment(b) for b in node.bases]
        bases += [f"{k.arg}={module.segment(k.value)}" for k in node.keywords]
        params = (
            f"[{', '.join(module.segment(t) for t in node.type_params)}]"
            if node.type_params
            else ""
        )
        heading = f"{decorators}class {node.name}{params}" + (
            f"({', '.join(bases)})" if bases else ""
        )
        init = self.index.member(q, "__init__")
        lines = [
            f"## {code(heading)}",
            self.path(q),
            *self.docstring(node),
            *self.fields(q),
        ]
        lines += self.raised_by(q, skip=(init,) if init else ())
        members: list[tuple[str, list[str]]] = []
        for sub in node.body:
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                member = self.method(q, sub)
                if member is not None:
                    members.append(member)
        for attr, function in self.index.bound(q).items():
            if not private(attr):
                members.append((attr, self.bound_method(q, attr, function)))
        members.sort(key=lambda m: (m[0] != "__init__", m[0].casefold(), m[0]))
        for _, written in members:
            lines += ["", *written]
        return lines

    def fields(self, q: str) -> list[str]:
        c = self.index.classes[q]
        module = c.module
        lines: list[str] = []
        for sub in c.node.body:
            if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                if not private(sub.target.id):
                    lines.append(f"- {code(self.constant(module, sub, sub.target.id))}")
            elif (
                isinstance(sub, ast.Assign)
                and len(sub.targets) == 1
                and isinstance(sub.targets[0], ast.Name)
            ):
                name = sub.targets[0].id
                if not private(name) and name not in self.index.bound(q):
                    lines.append(f"- {code(self.constant(module, sub, name))}")
            elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and decorated(
                sub, PROPERTIES
            ):
                if private(sub.name):
                    continue
                returns = f": {module.segment(sub.returns)}" if sub.returns else ""
                kind = (
                    "a cached property"
                    if decorated(sub, frozenset({"cached_property"}))
                    else "a property"
                )
                lines.append(f"- {code(sub.name + returns)}, {kind}")
                lines += [f"  {line}" for line in self.about(f"{q}.{sub.name}", sub)]
            elif (
                isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
                and sub.name == "__init__"
            ):
                for st in ast.walk(sub):
                    if (
                        isinstance(st, ast.AnnAssign)
                        and isinstance(st.target, ast.Attribute)
                        and isinstance(st.target.value, ast.Name)
                        and st.target.value.id == "self"
                        and not private(st.target.attr)
                    ):
                        lines.append(
                            f"- {code(f'{st.target.attr}: {module.segment(st.annotation)}')}"
                        )
        return lines

    def method(self, q: str, node: Def) -> tuple[str, list[str]] | None:
        if decorated(node, PROPERTIES | VALIDATORS):
            return None
        c = self.index.classes[q]
        if node.name == "__init__":
            heading = self.signature(c.module, node, c.name, drop=1)
            return node.name, [
                f"### {code(heading)}",
                *self.about(f"{q}.__init__", node),
            ]
        if private(node.name) or node.name == "__post_init__":
            return None
        static = decorated(node, frozenset({"staticmethod"}))
        heading = self.signature(
            c.module, node, f"{c.name}.{node.name}", drop=0 if static else 1
        )
        return node.name, [
            f"### {code(heading)}",
            *self.about(f"{q}.{node.name}", node),
        ]

    def bound_method(self, q: str, attr: str, function: str) -> list[str]:
        f: Function = self.index.functions[function]
        name = f"{self.index.classes[q].name}.{attr}"
        heading = self.signature(f.module, f.node, name, drop=1)
        return [
            f"### {code(heading)}",
            self.path(function),
            *self.about(function, f.node),
        ]


def page(index: Index, raises: Raises, package: str) -> str:
    return Page(index, raises, package).render()
