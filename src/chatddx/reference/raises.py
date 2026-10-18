import ast
from dataclasses import dataclass, replace

import griffe

from .code import Code, Def, decorated, private

VALIDATORS = frozenset(
    {"field_validator", "model_validator", "validator", "root_validator"}
)
VALIDATION = "pydantic.ValidationError"
CONVERSIONS = {ord("r"): "!r", ord("s"): "!s", ord("a"): "!a"}


@dataclass(frozen=True)
class Raised:
    exception: str
    message: str | None
    kind: str | None
    through: str | None = None
    validated: bool = False


def _first(raised: list[Raised]) -> tuple[Raised, ...]:
    found: dict[tuple[str, str | None, bool], Raised] = {}
    for r in raised:
        _ = found.setdefault((r.exception, r.message, r.validated), r)
    return tuple(found.values())


def _reraises(handler: ast.ExceptHandler) -> bool:
    pending: list[ast.AST] = list(handler.body)
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, ast.Raise) and (
            node.exc is None
            or (isinstance(node.exc, ast.Name) and node.exc.id == handler.name)
        ):
            return True
        pending += ast.iter_child_nodes(node)
    return False


class Raises:
    def __init__(self, code: Code) -> None:
        self.code: Code = code
        self._of: dict[tuple[str, str | None], tuple[Raised, ...]] = {}

    def of(
        self, function: griffe.Object, cls: griffe.Class | None
    ) -> tuple[Raised, ...]:
        key = (function.path, None if cls is None else cls.path)
        if key not in self._of:
            self._of[key] = ()
            node = self.code.node(function)
            assert not isinstance(node, ast.ClassDef)
            self._of[key] = _first(_Walker(self, function, node, cls).found)
        return self._of[key]

    def constructing(self, cls: griffe.Class) -> tuple[Raised, ...]:
        found: list[Raised] = []
        for name, member in cls.members.items():
            if not isinstance(member, griffe.Function) or not member.lineno:
                continue
            node = self.code.node(member)
            validated = decorated(node, VALIDATORS)
            if validated or name == "__post_init__":
                through = f"{cls.name}.{name}"
                for r in self.of(member, cls):
                    kind = VALIDATION if validated else r.kind
                    found.append(
                        replace(r, kind=kind, through=through, validated=validated)
                    )
        return _first(found)

    def caught(self, kind: str | None, caught: tuple[str, ...]) -> bool:
        return kind is not None and any(self.code.subclass(kind, h) for h in caught)


class _Walker:
    def __init__(
        self,
        raises: Raises,
        function: griffe.Object,
        node: Def,
        cls: griffe.Class | None,
    ) -> None:
        self.raises: Raises = raises
        self.code: Code = raises.code
        self.function: griffe.Object = function
        self.module: griffe.Module = function.module
        self.found: list[Raised] = []
        self.receivers: dict[str, griffe.Class] = {}
        args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        for arg in args:
            if arg.annotation is not None:
                held = self.code.get(
                    self.code.lookup(self.module, arg.annotation) or ""
                )
                if isinstance(held, griffe.Class):
                    self.receivers[arg.arg] = held
        static = decorated(node, frozenset({"staticmethod"}))
        if cls is not None and args and not static:
            self.receivers[args[0].arg] = cls
        for statement in node.body:
            self.visit(statement, ())

    def visit(self, node: ast.AST, caught: tuple[str, ...]) -> None:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        if isinstance(node, (ast.Try, ast.TryStar)):
            self.attempt(node, caught)
            return
        for child in ast.iter_child_nodes(node):
            self.visit(child, caught)
        if isinstance(node, ast.Raise):
            self.raised(node, caught)
        elif isinstance(node, ast.Call):
            self.called(node, caught)

    def attempt(self, node: ast.Try | ast.TryStar, caught: tuple[str, ...]) -> None:
        held: list[str] = []
        for handler in node.handlers:
            if _reraises(handler):
                continue
            if handler.type is None:
                held.append("builtins.BaseException")
            else:
                held += self.code.handled(self.module, handler.type)
        for statement in node.body:
            self.visit(statement, (*caught, *held))
        for handler in node.handlers:
            for statement in handler.body:
                self.visit(statement, caught)
        for statement in [*node.orelse, *node.finalbody]:
            self.visit(statement, caught)

    def raised(self, node: ast.Raise, caught: tuple[str, ...]) -> None:
        if node.exc is None:
            return
        target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        kind = self.code.lookup(self.module, target)
        if kind is None or self.raises.caught(kind, caught):
            return
        message = None
        if isinstance(node.exc, ast.Call) and node.exc.args:
            message = self.message(node.exc.args[0])
        self.found.append(
            Raised(self.code.segment(self.function, target), message, kind)
        )

    def called(self, node: ast.Call, caught: tuple[str, ...]) -> None:
        helper = self.helper(node.func)
        if helper is None:
            return
        function, cls, through = helper
        for r in self.raises.of(function, cls):
            if not self.raises.caught(r.kind, caught):
                self.found.append(replace(r, through=through))

    def helper(
        self, func: ast.expr
    ) -> tuple[griffe.Object, griffe.Class | None, str] | None:
        if isinstance(func, ast.Name) and private(func.id):
            found = self.code.get(self.code.lookup(self.module, func) or "")
            if isinstance(found, griffe.Function) and isinstance(
                found.parent, griffe.Module
            ):
                return found, None, found.name
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in self.receivers
            and private(func.attr)
        ):
            found = self.code.member(self.receivers[func.value.id], func.attr)
            if isinstance(found, griffe.Function) and isinstance(
                found.parent, griffe.Class
            ):
                return found, found.parent, f"{found.parent.name}.{found.name}"
        return None

    def message(self, node: ast.expr) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value.replace("\n", "\\n")
        if isinstance(node, ast.JoinedStr):
            return "".join(self.message(v) for v in node.values)
        if isinstance(node, ast.FormattedValue):
            conversion = CONVERSIONS.get(node.conversion, "")
            return f"{{{self.code.segment(self.function, node.value)}{conversion}}}"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.message(node.left) + self.message(node.right)
        if isinstance(node, (ast.Name, ast.Attribute)) and (
            text := self.code.text(self.module, node)
        ):
            return text
        return f"{{{self.code.segment(self.function, node)}}}"
