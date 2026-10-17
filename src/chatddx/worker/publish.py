import logging
import threading
import time
from uuid import UUID

import psycopg
from pydantic import JsonValue

from chatddx.api import schemas
from chatddx.api.events import Named, judged_of, said_of
from chatddx.bench import ScoringEvent
from chatddx.runner.run import Event, ItemEnded
from chatddx.store.notify import LIMIT, channel, tell
from chatddx.store.store import Connection

log = logging.getLogger(__name__)

# Deltas wait this long, in seconds, to go out together.
EVERY = 0.1

type _Delta = schemas.ItemDeltaData | schemas.JudgeDeltaData


class Publisher:
    def __init__(self, conn: Connection, run: UUID) -> None:
        self._conn: Connection = conn
        self._run: UUID = run
        self._guard: threading.Lock = threading.Lock()
        self._held: list[tuple[str, _Delta]] = []
        self._size: int = 0
        self._sent: float = time.monotonic()
        self._broken: bool = False

    def run_event(self, event: Event) -> None:
        if isinstance(event, ItemEnded):
            self._drop(event.item.key.case, event.item.key.replicate)
        elif (said := said_of(event)) is not None:
            self.put(said)

    def scoring_event(self, event: ScoringEvent) -> None:
        if (said := judged_of(event)) is not None:
            self.put(said)

    def put(self, said: Named) -> None:
        name, data = said
        with self._guard:
            if not isinstance(data, schemas.ItemDeltaData | schemas.JudgeDeltaData):
                self._flush(said)
                return
            self._delta(name, data)
            if self._size >= LIMIT or time.monotonic() - self._sent >= EVERY:
                self._flush()

    def close(self) -> None:
        with self._guard:
            self._flush()

    def _delta(self, name: str, data: _Delta) -> None:
        self._size += len(data.text)
        for at in range(len(self._held) - 1, -1, -1):
            held_name, held = self._held[at]
            if _key(held_name, held) != _key(name, data):
                continue
            if held.kind == data.kind:
                merged = {"text": held.text + data.text, "tokens": data.tokens}
                self._held[at] = (name, held.model_copy(update=merged))
                return
            break
        self._held.append((name, data))

    # An item's row tells how it ended, so its deltas still held go unsaid.
    def _drop(self, case: str, replicate: int) -> None:
        with self._guard:
            self._held = [
                (name, data)
                for name, data in self._held
                if _key(name, data) != ("item.delta", case, replicate)
            ]

    def _flush(self, *said: Named) -> None:
        held, self._held, self._size = self._held, [], 0
        self._sent = time.monotonic()
        told: list[tuple[str, JsonValue]] = [
            (name, data.model_dump(mode="json")) for name, data in (*held, *said)
        ]
        if not told or self._broken:
            return
        try:
            tell(self._conn, self._run, told)
        except psycopg.Error:
            log.exception(
                "what %s says as it happens can't be published", channel(self._run)
            )
            self._broken = True


def _key(name: str, data: _Delta) -> tuple[str, str, int]:
    return name, data.case, data.replicate
