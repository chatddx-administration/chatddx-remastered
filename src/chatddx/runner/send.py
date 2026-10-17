import threading
import time
from collections.abc import Callable, Generator, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from pydantic import JsonValue

from chatddx.factors.response import REASONING, reasoning
from chatddx.factors.trial import Execution
from chatddx.ledger import Call, fingerprint_request

from .wire import Chunk, Rejected, assemble, post

STREAM: dict[str, JsonValue] = {
    "stream": True,
    "stream_options": {"include_usage": True},
}
STOPPED = "stopped"


@dataclass(frozen=True)
class Delta:
    kind: Literal["reasoning", "content", "tool_call"]
    text: str
    tokens: int


class Stopped(Exception):
    def __init__(self, call: Call) -> None:
        self.call: Call = call
        super().__init__(STOPPED)


class Halt:
    def __init__(self) -> None:
        self._set: threading.Event = threading.Event()
        self._guard: threading.Lock = threading.Lock()
        self._watched: set[Callable[[], None]] = set()

    def set(self) -> None:
        with self._guard:
            self._set.set()
            watched = list(self._watched)
        for interrupt in watched:
            interrupt()

    def is_set(self) -> bool:
        return self._set.is_set()

    def wait(self, timeout: float) -> bool:
        return self._set.wait(timeout)

    @contextmanager
    def watching(self, interrupt: Callable[[], None]) -> Generator[None]:
        with self._guard:
            self._watched.add(interrupt)
            halted = self._set.is_set()
        if halted:
            interrupt()
        try:
            yield
        finally:
            with self._guard:
                self._watched.discard(interrupt)


def _now() -> datetime:
    return datetime.now(UTC)


def _deltas(chunk: Chunk) -> Iterator[tuple[Delta, int]]:
    choices = chunk.get("choices")
    for choice in choices if isinstance(choices, list) else []:
        if not isinstance(choice, dict) or choice.get("index", 0) != 0:
            continue
        delta = choice.get("delta")
        said = delta if isinstance(delta, dict) else {}
        thought = reasoning(said)
        found: list[Delta] = []
        for key, value in said.items():
            if key in REASONING:
                if thought is not None:
                    found.append(Delta("reasoning", thought, 0))
                    thought = None
            elif key == "content" and isinstance(value, str) and value:
                found.append(Delta("content", value, 0))
            elif key == "tool_calls" and isinstance(value, list):
                for call in value:
                    function = call.get("function") if isinstance(call, dict) else None
                    if isinstance(function, dict):
                        text = function.get("name") or function.get("arguments")
                        if isinstance(text, str) and text:
                            found.append(Delta("tool_call", text, 0))
        ids = choice.get("token_ids")
        count = len(ids) if isinstance(ids, list) else len(found)
        for n, d in enumerate(found):
            yield d, count if n == 0 else 0


def _retryable(status: int) -> bool:
    return status == 429 or status >= 500


def send(
    url: str,
    body: Mapping[str, JsonValue],
    *,
    execution: Execution | None = None,
    secret: str | None = None,
    on_delta: Callable[[Delta], None] | None = None,
    backoff: float = 1.0,
    halt: Halt | None = None,
    started_at: datetime | None = None,
) -> Call:
    execution = execution or Execution()
    request = fingerprint_request(dict(body))
    started = started_at or _now()
    attempts = 0
    received: list[Chunk] = []

    def call(
        status: int | None,
        error: str | None,
        response: dict[str, JsonValue] | None = None,
    ) -> Call:
        if response is None and received:
            response = assemble(received)
        return Call(
            request=request,
            started_at=started,
            finished_at=_now(),
            status=status,
            response=response,
            attempts=attempts,
            error=error,
        )

    try:
        while True:
            attempts += 1
            try:
                stream = post(
                    url,
                    {**body, **STREAM},
                    secret=secret,
                    timeout=execution.timeout_s,
                )
                break
            except Rejected as e:
                if attempts > execution.retries or not _retryable(e.status):
                    return call(e.status, str(e), e.body)
            except OSError as e:
                if attempts > execution.retries:
                    return call(None, f"{type(e).__name__}: {e}")
            delay = backoff * 2 ** (attempts - 1)
            if halt is None:
                time.sleep(delay)
            elif halt.wait(delay):
                raise Stopped(call(None, STOPPED))
    except KeyboardInterrupt:
        raise Stopped(call(None, STOPPED)) from None

    limit = execution.whitespace_limit
    deadline = (
        None if execution.timeout_s is None else time.monotonic() + execution.timeout_s
    )
    tokens = blank = 0
    error: str | None = None
    watching: AbstractContextManager[None] = (
        nullcontext() if halt is None else halt.watching(stream.interrupt)
    )
    with stream, watching:
        try:
            for chunk in stream:
                received.append(chunk)
                for delta, count in _deltas(chunk):
                    tokens += count
                    whitespace = delta.kind == "content" and not delta.text.strip()
                    blank = blank + count if whitespace else 0
                    if on_delta is not None:
                        on_delta(Delta(delta.kind, delta.text, tokens))
                if halt is not None and halt.is_set():
                    raise Stopped(call(stream.status, STOPPED))
                if limit is not None and blank >= limit:
                    error = f"stopped: nothing but whitespace for {blank} tokens"
                    break
                if deadline is not None and time.monotonic() > deadline:
                    error = f"stopped: no end after {execution.timeout_s} s"
                    break
        except KeyboardInterrupt:
            raise Stopped(call(stream.status, STOPPED)) from None
        except (Rejected, OSError, ValueError) as e:
            if halt is not None and halt.is_set():
                raise Stopped(call(stream.status, STOPPED)) from None
            error = f"{type(e).__name__}: {e}"
    return call(stream.status, error)
