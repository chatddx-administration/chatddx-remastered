import ast
import builtins
import importlib
from dataclasses import dataclass
from pathlib import Path

type Def = ast.FunctionDef | ast.AsyncFunctionDef

VALIDATORS = frozenset(
    {"field_validator", "model_validator", "validator", "root_validator"}
)


@dataclass(frozen=True)
class Module:
    name: str
    path: Path
    source: str
    tree: ast.Module
    imports: dict[str, str]

    def segment(self, node: ast.AST) -> str:
        written = ast.get_source_segment(self.source, node)
        if written is None or "\n" in written:
            return ast.unparse(node)
        return written


@dataclass(frozen=True)
class Function:
    name: str
    module: Module
    node: Def
    cls: str | None


@dataclass(frozen=True)
class Class:
    name: str
    module: Module
    node: ast.ClassDef


def decorated(node: Def | ast.ClassDef, names: frozenset[str]) -> bool:
    for d in node.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        if isinstance(target, ast.Name) and target.id in names:
            return True
        if isinstance(target, ast.Attribute) and target.attr in names:
            return True
    return False


def _module_name(root: Path, path: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _imports(name: str, path: Path, tree: ast.Module) -> dict[str, str]:
    package = name.split(".") if path.name == "__init__.py" else name.split(".")[:-1]
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            base = [*package[: len(package) - node.level + 1]] if node.level else []
            source = ".".join([*base, *([node.module] if node.module else [])])
            for alias in node.names:
                found[alias.asname or alias.name] = f"{source}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    found[alias.asname] = alias.name
                else:
                    head = alias.name.split(".")[0]
                    found[head] = head
    return found


class Index:
    def __init__(self, root: Path) -> None:
        self.root: Path = root
        self.modules: dict[str, Module] = {}
        self.functions: dict[str, Function] = {}
        self.classes: dict[str, Class] = {}
        self.constants: dict[str, tuple[Module, ast.expr]] = {}
        self.packages: set[str] = set()
        for path in sorted(root.rglob("*.py")):
            if "test" in path.relative_to(root).parts:
                continue
            source = path.read_text()
            tree = ast.parse(source, str(path))
            name = _module_name(root, path)
            module = Module(name, path, source, tree, _imports(name, path, tree))
            self.modules[name] = module
            self.packages.add(name.split(".")[0])
            for node in tree.body:
                self._define(module, node)

    def _define(self, module: Module, node: ast.stmt) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            q = f"{module.name}.{node.name}"
            self.functions[q] = Function(node.name, module, node, None)
        elif isinstance(node, ast.ClassDef):
            q = f"{module.name}.{node.name}"
            self.classes[q] = Class(node.name, module, node)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.functions[f"{q}.{sub.name}"] = Function(
                        sub.name, module, sub, q
                    )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.constants[f"{module.name}.{target.id}"] = (module, node.value)

    def canonical(self, q: str) -> str:
        return self._canonical(q, frozenset())

    def _canonical(self, q: str, seen: frozenset[str]) -> str:
        if q in self.functions or q in self.classes or q in self.modules or q in seen:
            return q
        module, _, name = q.rpartition(".")
        if module in self.modules and name in self.modules[module].imports:
            return self._canonical(self.modules[module].imports[name], seen | {q})
        if module and module not in self.modules:
            resolved = self._canonical(module, seen | {q})
            if resolved != module:
                return self._canonical(f"{resolved}.{name}", seen | {q})
        return q

    def owner(self, q: str) -> str | None:
        while q and q not in self.modules:
            q = q.rpartition(".")[0]
        return q or None

    def text(self, q: str | None) -> str | None:
        if q not in self.constants:
            return None
        value = self.constants[q][1]
        return (
            value.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
            else None
        )

    def resolve(self, module: Module, expr: ast.expr) -> str | None:
        if isinstance(expr, ast.Name):
            local = f"{module.name}.{expr.id}"
            if (
                local in self.functions
                or local in self.classes
                or local in self.constants
            ):
                return local
            if expr.id in module.imports:
                return self.canonical(module.imports[expr.id])
            if hasattr(builtins, expr.id):
                return f"builtins.{expr.id}"
            return None
        if isinstance(expr, ast.Attribute):
            base = self.resolve(module, expr.value)
            return None if base is None else self.canonical(f"{base}.{expr.attr}")
        if isinstance(expr, ast.Subscript):
            return self.resolve(module, expr.value)
        return None

    def annotated(self, module: Module, annotation: ast.expr | None) -> str | None:
        if annotation is None:
            return None
        if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            annotation = ast.parse(annotation.value, mode="eval").body
        if isinstance(annotation, ast.BinOp):
            return self.annotated(module, annotation.left) or self.annotated(
                module, annotation.right
            )
        q = self.resolve(module, annotation)
        return q if q in self.classes else None

    def bases(self, cls: str) -> list[str]:
        c = self.classes[cls]
        return [b for b in (self.resolve(c.module, x) for x in c.node.bases) if b]

    def mro(self, cls: str) -> list[str]:
        order = [cls]
        for base in self.bases(cls):
            if base in self.classes:
                order += [b for b in self.mro(base) if b not in order]
        return order

    def member(self, cls: str, name: str) -> str | None:
        for c in self.mro(cls):
            if f"{c}.{name}" in self.functions:
                return f"{c}.{name}"
            bound = self.bound(c).get(name)
            if bound is not None:
                return bound
        return None

    def bound(self, cls: str) -> dict[str, str]:
        c = self.classes[cls]
        found: dict[str, str] = {}
        for sub in c.node.body:
            if (
                isinstance(sub, ast.Assign)
                and len(sub.targets) == 1
                and isinstance(sub.targets[0], ast.Name)
            ):
                q = self.resolve(c.module, sub.value)
                if q in self.functions and self.functions[q].cls is None:
                    found[sub.targets[0].id] = q
        return found

    def attributes(self, cls: str) -> dict[str, str]:
        found: dict[str, str] = {}
        for c in reversed(self.mro(cls)):
            module, node = self.classes[c].module, self.classes[c].node
            for sub in node.body:
                if isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                    if t := self.annotated(module, sub.annotation):
                        found[sub.target.id] = t
                elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    properties = frozenset({"property", "cached_property"})
                    if decorated(sub, properties) and (
                        t := self.annotated(module, sub.returns)
                    ):
                        found[sub.name] = t
                    if sub.name == "__init__":
                        for st in ast.walk(sub):
                            if (
                                isinstance(st, ast.AnnAssign)
                                and isinstance(st.target, ast.Attribute)
                                and (t := self.annotated(module, st.annotation))
                            ):
                                found[st.target.attr] = t
        return found

    # Compromise: the project is read, never imported, which would take its environment;
    # a library is imported, for the bases of the exceptions it raises.
    def runtime(self, q: str) -> type | None:
        module, _, name = q.rpartition(".")
        if not module or module.split(".")[0] in self.packages:
            return None
        try:
            found = getattr(importlib.import_module(module), name)
        except (ImportError, AttributeError):
            return None
        return found if isinstance(found, type) else None

    def subclass(self, q: str, of: str) -> bool:
        if q == of:
            return True
        if q in self.classes:
            return any(self.subclass(b, of) for b in self.bases(q))
        found, base = self.runtime(q), self.runtime(of)
        return found is not None and base is not None and issubclass(found, base)

    def handled(self, module: Module, expr: ast.expr) -> list[str]:
        if isinstance(expr, ast.Tuple):
            return [t for e in expr.elts for t in self.handled(module, e)]
        q = self.resolve(module, expr)
        if q in self.constants:
            held, value = self.constants[q]
            return self.handled(held, value)
        return [] if q is None else [q]
