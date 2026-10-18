import ast
from dataclasses import dataclass, field, replace

from .index import VALIDATORS, Index, Module, decorated

VALIDATION = "pydantic.ValidationError"
CONVERSIONS = {ord("r"): "!r", ord("s"): "!s", ord("a"): "!a"}


@dataclass(frozen=True)
class Raised:
    exception: str
    said: str | None
    validated: bool = False

    @property
    def kind(self) -> str:
        return VALIDATION if self.validated else self.exception


@dataclass(frozen=True)
class Call:
    callee: str
    caught: tuple[str, ...]
    validated: bool = False
    inlined: bool = False


@dataclass
class Body:
    raised: list[Raised] = field(default_factory=list[Raised])
    calls: list[Call] = field(default_factory=list[Call])


@dataclass(frozen=True)
class Shown:
    raised: tuple[Raised, ...]
    via: frozenset[str]


def _piece(index: Index, module: Module, node: ast.expr) -> tuple[str, bool]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, True
    if isinstance(node, ast.JoinedStr):
        return "".join(_piece(index, module, v)[0] for v in node.values), True
    if isinstance(node, ast.FormattedValue):
        return (
            f"<{module.segment(node.value)}{CONVERSIONS.get(node.conversion, '')}>",
            True,
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, text = _piece(index, module, node.left)
        right, also = _piece(index, module, node.right)
        return left + right, text or also
    if isinstance(node, (ast.Name, ast.Attribute)) and (
        constant := index.text(index.resolve(module, node))
    ):
        return constant, True
    return f"<{module.segment(node)}>", False


def said(index: Index, module: Module, call: ast.Call) -> str:
    args: list[str] = []
    for arg in call.args:
        text, is_text = _piece(index, module, arg)
        args.append(
            f'"{text}"'.replace("\n", "\\n") if is_text else module.segment(arg)
        )
    args += [f"{k.arg}={module.segment(k.value)}" for k in call.keywords]
    return ", ".join(args)


def _reraises(handler: ast.ExceptHandler) -> bool:
    for node in _own(handler.body):
        if isinstance(node, ast.Raise) and (
            node.exc is None
            or (isinstance(node.exc, ast.Name) and node.exc.id == handler.name)
        ):
            return True
    return False


def _own(body: list[ast.stmt]) -> list[ast.AST]:
    found: list[ast.AST] = []
    pending: list[ast.AST] = list(body)
    while pending:
        node = pending.pop()
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        found.append(node)
        pending += ast.iter_child_nodes(node)
    return found


class _Walker:
    def __init__(self, index: Index, q: str) -> None:
        function = index.functions[q]
        self.index: Index = index
        self.module: Module = function.module
        self.body: Body = Body()
        self.types: dict[str, str] = {}
        args = function.node.args
        positional = [*args.posonlyargs, *args.args]
        for arg in [*positional, *args.kwonlyargs]:
            if found := index.annotated(self.module, arg.annotation):
                self.types[arg.arg] = found
        static = decorated(function.node, frozenset({"staticmethod"}))
        if function.cls is not None and positional and not static:
            self.types[positional[0].arg] = function.cls
        for statement in function.node.body:
            self.visit(statement, ())

    def visit(self, node: ast.AST, caught: tuple[str, ...]) -> None:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            return
        if isinstance(node, (ast.Try, ast.TryStar)):
            self.attempt(node, caught)
            return
        if isinstance(node, ast.Raise):
            self.raised(node, caught)
        elif isinstance(node, ast.Call):
            self.call(node, caught)
        for child in ast.iter_child_nodes(node):
            if not (
                isinstance(node, ast.Raise)
                and child is node.exc
                and isinstance(child, ast.Call)
            ):
                self.visit(child, caught)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            self.assigned(node)

    def attempt(self, node: ast.Try | ast.TryStar, caught: tuple[str, ...]) -> None:
        held: list[str] = []
        for handler in node.handlers:
            if not _reraises(handler):
                held += self.handled(handler)
        for statement in node.body:
            self.visit(statement, (*caught, *held))
        for handler in node.handlers:
            for statement in handler.body:
                self.visit(statement, caught)
        for statement in [*node.orelse, *node.finalbody]:
            self.visit(statement, caught)

    def handled(self, handler: ast.ExceptHandler) -> list[str]:
        if handler.type is None:
            return ["builtins.BaseException"]
        return self.index.handled(self.module, handler.type)

    def raised(self, node: ast.Raise, caught: tuple[str, ...]) -> None:
        exc = node.exc
        if exc is None:
            return
        if isinstance(exc, ast.Call):
            for arg in [*exc.args, *(k.value for k in exc.keywords)]:
                self.visit(arg, caught)
            q = self.index.resolve(self.module, exc.func)
            if q in self.index.functions:
                function = self.index.functions[q]
                found = self.index.annotated(function.module, function.node.returns)
                raised = None if found is None else Raised(found, None)
            else:
                raised = (
                    None if q is None else Raised(q, said(self.index, self.module, exc))
                )
        elif isinstance(exc, ast.Name) and exc.id in self.types:
            raised = Raised(self.types[exc.id], None)
        else:
            q = self.index.resolve(self.module, exc)
            raised = None
            if q is not None and (q in self.index.classes or self.index.runtime(q)):
                raised = Raised(q, None)
        if raised is not None and not self.caught(raised.kind, caught):
            self.body.raised.append(raised)

    def caught(self, kind: str, caught: tuple[str, ...]) -> bool:
        return any(self.index.subclass(kind, h) for h in caught)

    def call(self, node: ast.Call, caught: tuple[str, ...]) -> None:
        if (callee := self.target(node.func)) is not None:
            self.body.calls.append(Call(callee, caught))

    def assigned(self, node: ast.Assign | ast.AnnAssign) -> None:
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if not isinstance(target, ast.Name) or (
            isinstance(node, ast.Assign) and len(node.targets) > 1
        ):
            return
        found = (
            self.index.annotated(self.module, node.annotation)
            if isinstance(node, ast.AnnAssign)
            else None
        )
        if found is None and node.value is not None:
            found = self.type_of(node.value)
        if found is None:
            _ = self.types.pop(target.id, None)
        else:
            self.types[target.id] = found

    def target(self, func: ast.expr) -> str | None:
        if isinstance(func, ast.Attribute) and (owner := self.type_of(func.value)):
            return self.index.member(owner, func.attr)
        if isinstance(func, ast.Name) and func.id in self.types:
            return None
        q = self.index.resolve(self.module, func)
        return q if q in self.index.functions or q in self.index.classes else None

    def type_of(self, expr: ast.expr) -> str | None:
        if isinstance(expr, ast.Name):
            return self.types.get(expr.id)
        if isinstance(expr, ast.Attribute):
            owner = self.type_of(expr.value)
            return (
                None if owner is None else self.index.attributes(owner).get(expr.attr)
            )
        if isinstance(expr, ast.Await):
            return self.type_of(expr.value)
        if isinstance(expr, ast.Call):
            callee = self.target(expr.func)
            if callee in self.index.classes:
                return callee
            if callee in self.index.functions:
                function = self.index.functions[callee]
                if (
                    self.index.resolve(
                        function.module, function.node.returns or ast.Constant(None)
                    )
                    == "typing.Self"
                ):
                    return function.cls
                return self.index.annotated(function.module, function.node.returns)
        return None


def _constructor(index: Index, cls: str) -> Body:
    body = Body()
    if (init := index.member(cls, "__init__")) is not None:
        body.calls.append(Call(init, ()))
    if (post := index.member(cls, "__post_init__")) is not None:
        body.calls.append(Call(post, (), inlined=True))
    for c in index.mro(cls):
        for node in index.classes[c].node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and decorated(
                node, VALIDATORS
            ):
                body.calls.append(
                    Call(f"{c}.{node.name}", (), validated=True, inlined=True)
                )
    return body


def private(q: str) -> bool:
    return any(
        p.startswith("_") and not (p.startswith("__") and p.endswith("__"))
        for p in q.split(".")
    )


class Raises:
    def __init__(self, index: Index) -> None:
        self.index: Index = index
        self.bodies: dict[str, Body] = {
            q: _Walker(index, q).body for q in index.functions
        }
        self.bodies |= {q: _constructor(index, q) for q in index.classes}
        self.escaping: dict[str, set[str]] = {
            q: {r.kind for r in body.raised} for q, body in self.bodies.items()
        }
        self._subclass: dict[tuple[str, str], bool] = {}
        self._shown: dict[str, Shown] = {}
        changed = True
        while changed:
            changed = False
            for q, body in self.bodies.items():
                for call in body.calls:
                    for kind in list(self.escaping.get(call.callee, ())):
                        kind = VALIDATION if call.validated else kind
                        if kind not in self.escaping[q] and not self.caught(
                            kind, call.caught
                        ):
                            self.escaping[q].add(kind)
                            changed = True

    def caught(self, kind: str, caught: tuple[str, ...]) -> bool:
        for handler in caught:
            key = (kind, handler)
            if key not in self._subclass:
                self._subclass[key] = self.index.subclass(kind, handler)
            if self._subclass[key]:
                return True
        return False

    def escapes(self, q: str, caught: tuple[str, ...]) -> bool:
        return any(not self.caught(kind, caught) for kind in self.escaping.get(q, ()))

    def shown(self, q: str) -> Shown:
        if q not in self._shown:
            self._shown[q] = self._show(q, frozenset())
        return self._shown[q]

    def _show(self, q: str, within: frozenset[str]) -> Shown:
        body = self.bodies[q]
        raised = list(body.raised)
        via: set[str] = set()
        for call in body.calls:
            if call.callee == q or call.callee in within:
                continue
            if call.inlined or call.validated or private(call.callee):
                inner = self._show(call.callee, within | {q})
                for r in inner.raised:
                    r = replace(r, validated=True) if call.validated else r
                    if not self.caught(r.kind, call.caught):
                        raised.append(r)
                via |= {v for v in inner.via if self.escapes(v, call.caught)}
            elif self.escapes(call.callee, call.caught):
                via.add(call.callee)
        return Shown(tuple(dict.fromkeys(raised)), frozenset(via))
