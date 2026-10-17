import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import count
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import TupleRow
from pydantic import JsonValue, TypeAdapter

WORKERS = "worker"
ROWS = "rows"
JOB = "job "

# NOTIFY refuses a payload of 8000 bytes or more. Payloads are ASCII, so a character is
# a byte.
LIMIT = 7900
_PART = LIMIT - 64

type Said = list[tuple[str, JsonValue]]

_SAID: TypeAdapter[Said] = TypeAdapter(Said)

_MESSAGES: Iterator[int] = count()


@dataclass(frozen=True)
class Rows:
    pass


@dataclass(frozen=True)
class JobChanged:
    status: str


@dataclass(frozen=True)
class Events:
    said: Said


type Message = Rows | JobChanged | Events


def channel(run: UUID) -> str:
    return f"run.{run}"


def _text(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _payloads(said: Iterable[tuple[str, JsonValue]], ids: Iterator[int]) -> list[str]:
    packed: list[list[str]] = [[]]
    size = 2
    for name, data in said:
        text = _text([name, data])
        if packed[-1] and size + 1 + len(text) > LIMIT:
            packed.append([])
            size = 2
        size += len(text) + (1 if packed[-1] else 0)
        packed[-1].append(text)
    found: list[str] = []
    for batch in packed:
        if not batch:
            continue
        whole = f"[{','.join(batch)}]"
        if len(whole) <= LIMIT:
            found.append(whole)
            continue
        message = next(ids)
        parts = [whole[at : at + _PART] for at in range(0, len(whole), _PART)]
        found.extend(f"~{message} {i} {len(parts)}\n{p}" for i, p in enumerate(parts))
    return found


def tell(
    conn: psycopg.Connection[TupleRow],
    run: UUID,
    said: Iterable[tuple[str, JsonValue]],
) -> None:
    with conn.transaction():
        for payload in _payloads(said, _MESSAGES):
            _ = conn.execute("SELECT pg_notify(%s, %s)", (channel(run), payload))


def listen(conn: psycopg.Connection[TupleRow], *channels: str) -> None:
    for name in channels:
        _ = conn.execute(sql.SQL("LISTEN {}").format(sql.Identifier(name)))


def unlisten(conn: psycopg.Connection[TupleRow], *channels: str) -> None:
    for name in channels:
        _ = conn.execute(sql.SQL("UNLISTEN {}").format(sql.Identifier(name)))


class Assembler:
    def __init__(self) -> None:
        self._parts: dict[tuple[str, int], tuple[str, list[str]]] = {}

    def message(self, channel: str, pid: int, payload: str) -> Message | None:
        if payload == ROWS:
            return Rows()
        if payload.startswith(JOB):
            return JobChanged(payload.removeprefix(JOB))
        if payload.startswith("~"):
            head, _, text = payload[1:].partition("\n")
            message, at, of = head.split()
            key = (channel, pid)
            if at == "0":
                self._parts[key] = (message, [])
            held = self._parts.get(key)
            if held is None or held[0] != message or len(held[1]) != int(at):
                _ = self._parts.pop(key, None)
                return None
            held[1].append(text)
            if len(held[1]) < int(of):
                return None
            del self._parts[key]
            payload = "".join(held[1])
        return Events(_SAID.validate_json(payload))
