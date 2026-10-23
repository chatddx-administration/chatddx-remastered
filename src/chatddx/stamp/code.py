import ast
import builtins
import importlib
import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import griffe

type Def = ast.FunctionDef | ast.AsyncFunctionDef
type Node = Def | ast.ClassDef
type Spanned = ast.expr | ast.stmt | ast.type_param

_LINE = re.compile(r"(.*?(?:\r\n|\n|\r|$))")


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


def _assigned(node: ast.AST) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return node.name.id if isinstance(node, ast.TypeAlias) else None


def _named(
    node: ast.AST, prefix: str, fields: bool
) -> Iterator[tuple[str, int, int, int]]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = prefix + child.name
            first = min([child.lineno, *(d.lineno for d in child.decorator_list)])
            yield name, first, child.end_lineno or first, child.col_offset
            yield from _named(child, f"{name}.", isinstance(child, ast.ClassDef))
        elif fields and isinstance(child, ast.stmt) and (name := _assigned(child)):
            yield (
                prefix + name,
                child.lineno,
                child.end_lineno or child.lineno,
                child.col_offset,
            )
        else:
            yield from _named(child, prefix, fields)


@dataclass(frozen=True)
class File:
    source: str
    tree: ast.Module

    @cached_property
    def nodes(self) -> dict[int, Node]:
        found: dict[int, Node] = {}
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for line in [node.lineno, *(d.lineno for d in node.decorator_list)]:
                    found[line] = node
        return found

    @cached_property
    def names(self) -> list[tuple[str, int, int, int]]:
        return list(_named(self.tree, "", fields=True))

    @cached_property
    def lines(self) -> list[str]:
        return [m[0] for m in _LINE.finditer(self.source)]

    # Optimization: ast.get_source_segment, but over lines split once, where it splits
    # the whole source on each call.
    def segment(self, node: Spanned, padded: bool = False) -> str | None:
        first, last = node.lineno - 1, node.end_lineno
        begun, ended = node.col_offset, node.end_col_offset
        if last is None or ended is None:
            return None
        head = self.lines[first].encode()
        if first == last - 1:
            return head[begun:ended].decode()
        indent = (
            "".join(c if c in "\f\t" else " " for c in head[:begun].decode())
            if padded
            else ""
        )
        tail = self.lines[last - 1].encode()[:ended].decode()
        return "".join(
            [indent + head[begun:].decode(), *self.lines[first + 1 : last - 1], tail]
        )


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
        self._files: dict[Path, File] = {}

    def file(self, path: Path) -> File:
        if path not in self._files:
            source = path.read_text()
            self._files[path] = File(source, ast.parse(source, str(path)))
        return self._files[path]

    def node(self, obj: griffe.Object) -> Node:
        assert isinstance(obj.filepath, Path) and obj.lineno is not None
        return self.file(obj.filepath).nodes[obj.lineno]

    def lines(self, obj: griffe.Object) -> list[str]:
        assert isinstance(obj.filepath, Path) and obj.lineno is not None
        held = self.file(obj.filepath).lines[
            obj.lineno - 1 : obj.endlineno or obj.lineno
        ]
        return [line.rstrip("\r\n") for line in held]

    def source(self, obj: griffe.Object, node: Spanned) -> str | None:
        assert isinstance(obj.filepath, Path)
        return self.file(obj.filepath).segment(node)

    def segment(self, obj: griffe.Object, node: Spanned) -> str:
        written = self.source(obj, node)
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
                self.named(e)
                for e in found.value.elements
                if isinstance(e, griffe.ExprName)
            ]
        return [] if path is None else [path]

    def named(self, expr: griffe.ExprName) -> str:
        path = expr.canonical_path
        return path if "." in path else f"builtins.{path}"

    def bases(self, cls: griffe.Class) -> list[str]:
        return [self.named(b) for b in cls.bases if isinstance(b, griffe.ExprName)]

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
