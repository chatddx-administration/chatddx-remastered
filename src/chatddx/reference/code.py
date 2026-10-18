import ast
import builtins
import importlib
from pathlib import Path

import griffe

type Def = ast.FunctionDef | ast.AsyncFunctionDef
type Node = Def | ast.ClassDef


def private(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


def decorated(node: Node, names: frozenset[str]) -> bool:
    for d in node.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        if isinstance(target, ast.Name) and target.id in names:
            return True
        if isinstance(target, ast.Attribute) and target.attr in names:
            return True
    return False


def _final(member: griffe.Object | griffe.Alias) -> str:
    if not isinstance(member, griffe.Alias):
        return member.path
    try:
        return member.final_target.path
    except (griffe.AliasResolutionError, griffe.CyclicAliasError):
        return member.target_path


class Code:
    def __init__(self, src: Path, package: str) -> None:
        self.src: Path = src
        loaded = griffe.load(
            package, search_paths=[src], resolve_aliases=True, resolve_external=False
        )
        assert isinstance(loaded, griffe.Module)
        self.root: griffe.Module = loaded
        self._files: dict[Path, tuple[str, dict[int, Node]]] = {}

    def _file(self, path: Path) -> tuple[str, dict[int, Node]]:
        if path not in self._files:
            source = path.read_text()
            nodes: dict[int, Node] = {}
            for node in ast.walk(ast.parse(source, str(path))):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    for line in [node.lineno, *(d.lineno for d in node.decorator_list)]:
                        nodes[line] = node
            self._files[path] = (source, nodes)
        return self._files[path]

    def node(self, obj: griffe.Object) -> Node:
        assert isinstance(obj.filepath, Path) and obj.lineno is not None
        return self._file(obj.filepath)[1][obj.lineno]

    def lines(self, obj: griffe.Object) -> list[str]:
        assert isinstance(obj.filepath, Path) and obj.lineno is not None
        source = self._file(obj.filepath)[0].splitlines()
        return source[obj.lineno - 1 : obj.endlineno or obj.lineno]

    def segment(self, obj: griffe.Object, node: ast.AST) -> str:
        assert isinstance(obj.filepath, Path)
        written = ast.get_source_segment(self._file(obj.filepath)[0], node)
        if written is None or "\n" in written:
            return ast.unparse(node)
        return written

    def get(self, path: str) -> griffe.Object | None:
        head, _, rest = path.partition(".")
        if head != self.root.name:
            return None
        try:
            found = self.root[rest] if rest else self.root
            return found.final_target if isinstance(found, griffe.Alias) else found
        except (KeyError, griffe.AliasResolutionError, griffe.CyclicAliasError):
            return None

    def lookup(self, module: griffe.Module, expr: ast.expr) -> str | None:
        if isinstance(expr, ast.Name):
            member = module.members.get(expr.id)
            if member is not None:
                return _final(member)
            return f"builtins.{expr.id}" if hasattr(builtins, expr.id) else None
        if isinstance(expr, ast.Attribute):
            base = self.lookup(module, expr.value)
            if base is None:
                return None
            found = self.get(base)
            if found is not None and expr.attr in found.members:
                return _final(found.members[expr.attr])
            return f"{base}.{expr.attr}"
        return None

    def text(self, module: griffe.Module, expr: ast.expr) -> str | None:
        found = self.get(self.lookup(module, expr) or "")
        if isinstance(found, griffe.Attribute) and isinstance(found.value, str):
            try:
                value = ast.literal_eval(found.value)
            except (ValueError, SyntaxError):
                return None
            return value if isinstance(value, str) else None
        return None

    def handled(self, module: griffe.Module, expr: ast.expr) -> list[str]:
        if isinstance(expr, ast.Tuple):
            return [t for e in expr.elts for t in self.handled(module, e)]
        path = self.lookup(module, expr)
        found = self.get(path or "")
        if isinstance(found, griffe.Attribute) and isinstance(
            found.value, griffe.ExprTuple
        ):
            return [
                self._named(e)
                for e in found.value.elements
                if isinstance(e, griffe.ExprName)
            ]
        return [] if path is None else [path]

    def _named(self, expr: griffe.ExprName) -> str:
        path = expr.canonical_path
        return path if "." in path else f"builtins.{path}"

    def bases(self, cls: griffe.Class) -> list[str]:
        return [self._named(b) for b in cls.bases if isinstance(b, griffe.ExprName)]

    def member(self, cls: griffe.Class, name: str) -> griffe.Object | None:
        if name in cls.members:
            found = cls.members[name]
            return found.final_target if isinstance(found, griffe.Alias) else found
        for base in self.bases(cls):
            if isinstance(found := self.get(base), griffe.Class) and (
                held := self.member(found, name)
            ):
                return held
        return None

    def subclass(self, path: str, of: str) -> bool:
        if path == of:
            return True
        found = self.get(path)
        if isinstance(found, griffe.Class):
            return any(self.subclass(b, of) for b in self.bases(found))
        held, base = self._runtime(path), self._runtime(of)
        return held is not None and base is not None and issubclass(held, base)

    # Compromise: the project is read, never imported, which would take its environment;
    # a library is imported, for the bases of the exceptions it raises.
    def _runtime(self, path: str) -> type | None:
        module, _, name = path.rpartition(".")
        if not module or module.split(".")[0] == self.root.name:
            return None
        try:
            found = getattr(importlib.import_module(module), name)
        except (ImportError, AttributeError):
            return None
        return found if isinstance(found, type) else None
