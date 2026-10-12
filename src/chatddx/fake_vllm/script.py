import json
import threading
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .served import Refused

FIELDS = frozenset(
    {"reasoning", "content", "tool_calls", "finish", "runaway", "hang_up", "status"}
)


@dataclass(frozen=True)
class Turn:
    reasoning: str | None = None
    content: str = ""
    calls: tuple[tuple[str, str], ...] = ()
    finish: str | None = None
    runaway: int = 0
    hang_up: int | None = None
    status: int | None = None


def _str(where: str, value: object) -> str:
    if not isinstance(value, str):
        raise Refused(f"{where} is text, not {value!r}")
    return value


def _count(where: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise Refused(f"{where} is a count, not {value!r}")
    return value


def _call(where: str, value: object) -> tuple[str, str]:
    if not isinstance(value, dict):
        raise Refused(f"{where} is a table of a name and arguments")
    held = cast(dict[str, object], value)
    if stray := set(held) - {"name", "arguments"}:
        raise Refused(f"{where} has no {sorted(stray)}")
    arguments = held.get("arguments", {})
    text = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return _str(f"{where}.name", held.get("name")), text


def turn(where: str, value: object) -> Turn:
    if not isinstance(value, dict):
        raise Refused(f"{where} is a table")
    held = cast(dict[str, Any], value)
    if stray := set(held) - FIELDS:
        raise Refused(f"{where} has no {sorted(stray)}")
    reasoning = held.get("reasoning")
    finish = held.get("finish")
    hang_up = held.get("hang_up")
    status = held.get("status")
    calls = held.get("tool_calls", [])
    if not isinstance(calls, list):
        raise Refused(f"{where}.tool_calls is a list")
    return Turn(
        reasoning=None if reasoning is None else _str(f"{where}.reasoning", reasoning),
        content=_str(f"{where}.content", held.get("content", "")),
        calls=tuple(
            _call(f"{where}.tool_calls[{n}]", c)
            for n, c in enumerate(cast(list[object], calls))
        ),
        finish=None if finish is None else _str(f"{where}.finish", finish),
        runaway=_count(f"{where}.runaway", held.get("runaway", 0)),
        hang_up=None if hang_up is None else _count(f"{where}.hang_up", hang_up),
        status=None if status is None else _count(f"{where}.status", status),
    )


# A script's file may hold keys of its reader's: src/chatddx/samples/sample.py.
class Script:
    def __init__(self, turns: Iterable[Turn]) -> None:
        self.turns: tuple[Turn, ...] = tuple(turns)
        self._next: int = 0
        self._lock: threading.Lock = threading.Lock()

    @classmethod
    def of(cls, data: dict[str, Any], where: str = "the script") -> "Script":
        turns = data.get("turn", [])
        if not isinstance(turns, list) or not turns:
            raise Refused(f"{where} has no [[turn]]")
        return cls(
            turn(f"{where}: turn {n + 1}", t)
            for n, t in enumerate(cast(list[object], turns))
        )

    @classmethod
    def load(cls, path: Path) -> "Script":
        with path.open("rb") as f:
            return cls.of(tomllib.load(f), str(path))

    def next(self) -> tuple[int, Turn] | None:
        with self._lock:
            if self._next >= len(self.turns):
                return None
            self._next += 1
            return self._next, self.turns[self._next - 1]
