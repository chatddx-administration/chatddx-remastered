import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from jsonschema import validators
from jsonschema.exceptions import relevance
from jsonschema.protocols import Validator
from pydantic import JsonValue

from chatddx.factors.base import Resolver, resolve
from chatddx.factors.request import (
    Skeleton,
    Tool,
    ToolCall,
    ToolOutput,
    next_request,
    tool_calls,
)
from chatddx.factors.trial import Execution
from chatddx.ledger import Call, ToolCode, ToolRun, Turn
from chatddx.rig import entry
from chatddx.tools.shipped import TOOLS

from . import send as sending
from .send import Delta


def _now() -> datetime:
    return datetime.now(UTC)


class _Refused(Exception):
    pass


class ToolStopped(Exception):
    def __init__(self, run: ToolRun) -> None:
        self.run: ToolRun = run
        super().__init__(sending.STOPPED)


@dataclass(frozen=True)
class Toolbox:
    functions: Mapping[str, Callable[..., object]]
    parameters: Mapping[str, Validator]
    answer: str | None
    max_rounds: int
    code: tuple[ToolCode, ...]

    def pending(self, call: Call) -> tuple[ToolCall, ...]:
        if call.error is not None or call.response is None:
            return ()
        calls = tool_calls(call.response)
        if any(c.name == self.answer for c in calls):
            return ()
        return calls

    def run(self, call: ToolCall) -> ToolRun:
        started = _now()
        error: str | None
        try:
            result, error = self._result(call), None
        except _Refused as e:
            error = str(e)
            result = f"error: {error}"
        except Exception as e:  # noqa: BLE001
            error = f"{type(e).__name__}: {e}"
            result = f"error: {error}"
        except KeyboardInterrupt:
            raise ToolStopped(
                ToolRun(
                    id=call.id,
                    name=call.name,
                    started_at=started,
                    finished_at=_now(),
                    result=f"error: {sending.STOPPED}",
                    error=sending.STOPPED,
                )
            ) from None
        return ToolRun(
            id=call.id,
            name=call.name,
            started_at=started,
            finished_at=_now(),
            result=result,
            error=error,
        )

    def _result(self, call: ToolCall) -> str:
        function = self.functions.get(call.name)
        if function is None:
            raise _Refused(f"no tool named {call.name!r}")
        try:
            arguments: JsonValue = json.loads(call.arguments)
        except ValueError as e:
            raise _Refused(f"the arguments aren't JSON: {e}") from None
        if not isinstance(arguments, dict):
            raise _Refused("the arguments aren't an object")
        errors = self.parameters[call.name].iter_errors(arguments)
        found = max(errors, key=relevance, default=None)
        if found is not None:
            raise _Refused(f"the arguments don't fit the parameters: {found.message}")
        result = function(**arguments)
        if not isinstance(result, str):
            raise _Refused(f"the tool returned {type(result).__name__}, not text")
        return result


def load(skeleton: Skeleton, get: Resolver) -> Toolbox | None:
    if skeleton.max_rounds is None:
        return None
    functions: dict[str, Callable[..., object]] = {}
    parameters: dict[str, Validator] = {}
    code: list[ToolCode] = []
    for ref in skeleton.tools:
        tool = resolve(get, ref, Tool)
        shipped = entry(TOOLS, tool.entry_point, tool.version)
        functions[tool.name] = shipped.function
        parameters[tool.name] = validators.validator_for(tool.parameters)(
            tool.parameters
        )
        code.append(ToolCode(tool=ref, version=shipped.version))
    contract = skeleton.contract
    return Toolbox(
        functions=functions,
        parameters=parameters,
        answer=contract.name if isinstance(contract, ToolOutput) else None,
        max_rounds=skeleton.max_rounds,
        code=tuple(code),
    )


@dataclass(frozen=True)
class Exchange:
    call: Call
    turns: tuple[Turn, ...] = ()
    stopped: bool = False


def converse(
    url: str,
    body: Mapping[str, JsonValue],
    toolbox: Toolbox | None,
    *,
    execution: Execution,
    secret: str | None,
    on_delta: Callable[[Delta], None],
    on_tool: Callable[[ToolRun], None],
    halt: sending.Halt | None = None,
    started_at: datetime | None = None,
) -> Exchange:
    def send(request: Mapping[str, JsonValue], at: datetime | None = None) -> Call:
        return sending.send(
            url,
            request,
            execution=execution,
            secret=secret,
            on_delta=on_delta,
            halt=halt,
            started_at=at,
        )

    def halted() -> bool:
        return halt is not None and halt.is_set()

    try:
        first = send(body, started_at)
    except sending.Stopped as stopped:
        return Exchange(stopped.call, stopped=True)
    # The round under way is always the last of turns, replaced whole as it grows, so an
    # interrupt between two statements finds it as far as it got.
    turns: list[Turn] = []
    previous = first
    try:
        while toolbox is not None and len(turns) < toolbox.max_rounds:
            calls = toolbox.pending(previous)
            if not calls:
                break
            at = len(turns)
            runs: tuple[ToolRun, ...] = ()
            for call in calls:
                if halted():
                    return Exchange(first, tuple(turns), stopped=True)
                try:
                    run = toolbox.run(call)
                except ToolStopped as e:
                    turns[at:] = [Turn(tools=(*runs, e.run))]
                    return Exchange(first, tuple(turns), stopped=True)
                runs = (*runs, run)
                turns[at:] = [Turn(tools=runs)]
                on_tool(run)
            if halted():
                return Exchange(first, tuple(turns), stopped=True)
            assert previous.response is not None
            body = next_request(body, previous.response, {r.id: r.result for r in runs})
            try:
                previous = send(body)
            except sending.Stopped as stopped:
                turns[at:] = [Turn(tools=runs, call=stopped.call)]
                return Exchange(first, tuple(turns), stopped=True)
            turns[at:] = [Turn(tools=runs, call=previous)]
    except KeyboardInterrupt:
        return Exchange(first, tuple(turns), stopped=True)
    return Exchange(first, tuple(turns))
