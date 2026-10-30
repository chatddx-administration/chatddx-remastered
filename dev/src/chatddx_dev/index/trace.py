import ast
from dataclasses import dataclass, replace

import griffe

from .code import Code, Def, decorated, private

VALIDATORS = frozenset(
    {"field_validator", "model_validator", "validator", "root_validator"}
)
_VALIDATION = "pydantic.ValidationError"
_CONVERSIONS = {ord("r"): "!r", ord("s"): "!s", ord("a"): "!a"}


@dataclass(frozen=True)
class Raised:
    exception: str
    message: str | None
    kind: str | None
    through: str | None = None
    validated: bool = False
    origin: str | None = None


@dataclass(frozen=True)
class Found:
    code: str
    message: str | None
    level: str | None = None
    through: str | None = None
    origin: str | None = None


@dataclass(frozen=True)
class Traced:
    raised: tuple[Raised, ...]
    found: tuple[Found, ...]


def _first(raised: list[Raised]) -> tuple[Raised, ...]:
    kept: dict[tuple[str, str | None, bool], Raised] = {}
    for r in raised:
        _ = kept.setdefault((r.exception, r.message, r.validated), r)
    return tuple(kept.values())


def _once(found: list[Found]) -> tuple[Found, ...]:
    kept: dict[tuple[str, str | None, str | None], Found] = {}
    for f in found:
        _ = kept.setdefault((f.code, f.message, f.level), f)
    return tuple(kept.values())


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


class Trace:
    def __init__(self, code: Code, finding: str, whoops: str) -> None:
        self.code: Code = code
        self.findings: tuple[str, str] = (finding, f"{finding}.of")
        self.whoops: str = whoops
        self._of: dict[tuple[str, str | None], Traced] = {}

    def of(self, function: griffe.Object, cls: griffe.Class | None) -> Traced:
        key = (function.path, None if cls is None else cls.path)
        if key not in self._of:
            self._of[key] = Traced((), ())
            node = self.code.node(function)
            assert not isinstance(node, ast.ClassDef)
            walked = _Walker(self, function, node, cls)
            self._of[key] = Traced(_first(walked.raised), _once(walked.found))
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
                for r in self.of(member, cls).raised:
                    kind = _VALIDATION if validated else r.kind
                    found.append(
                        replace(r, kind=kind, through=through, validated=validated)
                    )
        return _first(found)

    def caught(self, kind: str | None, caught: tuple[str, ...]) -> bool:
        return kind is not None and any(self.code.subclass(kind, h) for h in caught)


class _Walker:
    def __init__(
        self,
        trace: Trace,
        function: griffe.Object,
        node: Def,
        cls: griffe.Class | None,
    ) -> None:
        self.trace: Trace = trace
        self.code: Code = trace.code
        self.function: griffe.Object = function
        self.module: griffe.Module = function.module
        self.raised: list[Raised] = []
        self.found: list[Found] = []
        self.handlers: dict[str, str] = {}
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
            self.raising(node, caught)
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
            outer = dict(self.handlers)
            if handler.name is not None and handler.type is not None:
                self.handlers[handler.name] = self.code.segment(
                    self.function, handler.type
                )
            for statement in handler.body:
                self.visit(statement, caught)
            self.handlers = outer
        for statement in [*node.orelse, *node.finalbody]:
            self.visit(statement, caught)

    def raising(self, node: ast.Raise, caught: tuple[str, ...]) -> None:
        if node.exc is None:
            return
        target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        if isinstance(target, ast.Attribute) and target.attr == "of":
            target = target.value
        kind = self.code.lookup(self.module, target)
        exception, through = self.code.segment(self.function, target), None
        factory = self.code.get(kind or "")
        if isinstance(factory, griffe.Function):
            if not isinstance(factory.returns, griffe.ExprName):
                return
            exception, through = factory.returns.name, factory.name
            kind = self.code.named(factory.returns)
        if (
            kind is None
            or self.trace.caught(kind, caught)
            or self.code.subclass(kind, self.trace.whoops)
        ):
            return
        said = self.said(node.exc) if isinstance(node.exc, ast.Call) else None
        origin = self.origin(node.exc)
        self.raised.append(Raised(exception, said, kind, through, origin=origin))

    def called(self, node: ast.Call, caught: tuple[str, ...]) -> None:
        if self.code.lookup(self.module, node.func) in self.trace.findings:
            self.finding(node)
            return
        helper = self.helper(node.func)
        if helper is None:
            return
        function, cls, through = helper
        traced = self.trace.of(function, cls)
        for r in traced.raised:
            if not self.trace.caught(r.kind, caught):
                self.raised.append(replace(r, through=through))
        self.found += [replace(f, through=through) for f in traced.found]

    def finding(self, node: ast.Call) -> None:
        said = {k.arg: k.value for k in node.keywords if k.arg is not None}
        said |= dict(zip(("code", "message"), node.args, strict=False))
        if "code" not in said:
            return
        code = self.text(said["code"])
        level = None if "level" not in said else self.text(said["level"])
        if "level" in said and level is None:
            level = f"{{{self.code.segment(self.function, said['level'])}}}"
        message = None if "message" not in said else self.argument(said["message"])
        self.found.append(
            Found(
                code
                if code is not None
                else f"{{{self.code.segment(self.function, said['code'])}}}",
                message,
                None if level == "warning" else level,
                origin=self.origin(node),
            )
        )

    def origin(self, node: ast.expr) -> str | None:
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        return next((t for n, t in self.handlers.items() if n in names), None)

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

    def said(self, call: ast.Call) -> str | None:
        written = [self.argument(a) for a in call.args]
        for k in call.keywords:
            value = self.argument(k.value)
            written.append(f"**{value}" if k.arg is None else f"{k.arg}={value}")
        return ", ".join(written) or None

    def argument(self, node: ast.expr) -> str:
        if isinstance(node, ast.Tuple):
            return " / ".join(dict.fromkeys(self.argument(e) for e in node.elts))
        text = self.text(node)
        return self.code.segment(self.function, node) if text is None else f'"{text}"'

    def text(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value.replace("\n", "\\n")
        if isinstance(node, ast.JoinedStr):
            return "".join(self.text(v) or "" for v in node.values)
        if isinstance(node, ast.FormattedValue):
            conversion = _CONVERSIONS.get(node.conversion, "")
            return f"{{{self.code.segment(self.function, node.value)}{conversion}}}"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = self.text(node.left), self.text(node.right)
            if left is None and right is None:
                return None
            written = [
                self.code.segment(self.function, n) for n in (node.left, node.right)
            ]
            return (left or f"{{{written[0]}}}") + (right or f"{{{written[1]}}}")
        if isinstance(node, (ast.Name, ast.Attribute)):
            return self.code.text(self.module, node)
        return None
