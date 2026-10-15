import asyncio
import logging
import select
import socket
import threading
from collections import deque
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID

import psycopg
from psycopg import Notify, sql

from chatddx.store.notify import Assembler, Message, channel
from chatddx.store.store import Connection

log = logging.getLogger(__name__)

# How long, in seconds, the listener waits after losing its connection, and at most for
# anything to happen.
AGAIN = 1.0

# A stream this many messages behind drops what it holds and reads the ledger again.
BEHIND = 1000


@dataclass(frozen=True)
class Lagged:
    pass


type Heard = Message | Lagged


class Hearing:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self._heard: deque[Heard] = deque()
        self._ready: asyncio.Event = asyncio.Event()

    def put(self, heard: Heard) -> None:
        if len(self._heard) >= BEHIND:
            self._heard.clear()
            heard = Lagged()
        self._heard.append(heard)
        self._ready.set()

    async def next(self, timeout: float) -> list[Heard]:
        if not self._heard:
            self._ready.clear()
            _ = await asyncio.wait_for(self._ready.wait(), timeout)
        taken = list(self._heard)
        self._heard.clear()
        return taken


class Listener:
    def __init__(self, conninfo: str) -> None:
        self._conninfo: str = conninfo
        self._guard: threading.Lock = threading.Lock()
        self._hearing: dict[str, set[Hearing]] = {}
        self._asked: list[tuple[str, asyncio.Future[None]]] = []
        self._stopping: threading.Event = threading.Event()
        self._thread: threading.Thread | None = None
        self._waking: socket.socket | None = None

    @asynccontextmanager
    async def heard(self, run: UUID) -> AsyncGenerator[Hearing]:
        loop = asyncio.get_running_loop()
        hearing, listening = Hearing(loop), loop.create_future()
        name = channel(run)
        with self._guard:
            if self._thread is None:
                self._waking, woken = socket.socketpair()
                self._waking.setblocking(False)
                self._thread = threading.Thread(
                    target=self._listen,
                    args=(woken,),
                    name="chatddx-listener",
                    daemon=True,
                )
                self._thread.start()
            self._hearing.setdefault(name, set()).add(hearing)
            self._asked.append((name, listening))
            _wake(self._waking)
        try:
            await listening
            yield hearing
        finally:
            with self._guard:
                held = self._hearing.get(name, set())
                held.discard(hearing)
                if not held:
                    _ = self._hearing.pop(name, None)

    def stop(self) -> None:
        with self._guard:
            self._stopping.set()
            thread, waking = self._thread, self._waking
            self._thread = self._waking = None
        _wake(waking)
        if thread is not None:
            thread.join()
        if waking is not None:
            waking.close()
        self._stopping.clear()

    def _listen(self, woken: socket.socket) -> None:
        lost = False
        try:
            while not self._stopping.is_set():
                try:
                    with psycopg.connect(self._conninfo, autocommit=True) as conn:
                        self._serve(conn, woken, lost)
                except psycopg.Error:
                    log.exception("the listener lost its connection")
                lost = True
                _ = self._stopping.wait(AGAIN)
        finally:
            woken.close()

    def _serve(self, conn: Connection, woken: socket.socket, lost: bool) -> None:
        listening: set[str] = set()
        assembler = Assembler()
        if lost:
            self._tell_all(Lagged())
        while not self._stopping.is_set():
            self._follow(conn, listening)
            for notify in conn.notifies(timeout=0):
                self._dispatch(assembler, notify)
            ready, _, _ = select.select([conn.fileno(), woken], [], [], AGAIN)
            if woken in ready:
                _ = woken.recv(4096)

    def _follow(self, conn: Connection, listening: set[str]) -> None:
        with self._guard:
            wanted = set(self._hearing)
            asked, self._asked = self._asked, []
        for name in sorted(wanted - listening):
            _ = conn.execute(sql.SQL("LISTEN {}").format(sql.Identifier(name)))
        for name in sorted(listening - wanted):
            _ = conn.execute(sql.SQL("UNLISTEN {}").format(sql.Identifier(name)))
        listening.clear()
        listening.update(wanted)
        for _, future in asked:
            _soon(future.get_loop(), _listened, future)

    def _dispatch(self, assembler: Assembler, notify: Notify) -> None:
        message = assembler.message(notify.channel, notify.pid, notify.payload)
        if message is None:
            return
        with self._guard:
            hearing = list(self._hearing.get(notify.channel, ()))
        _tell(hearing, message)

    def _tell_all(self, heard: Heard) -> None:
        with self._guard:
            hearing = [h for held in self._hearing.values() for h in held]
        _tell(hearing, heard)


def _wake(waking: socket.socket | None) -> None:
    if waking is None:
        return
    try:
        _ = waking.send(b"\0")
    except OSError:
        pass


def _tell(hearing: list[Hearing], heard: Heard) -> None:
    for h in hearing:
        _soon(h.loop, h.put, heard)


def _soon[*A](
    loop: asyncio.AbstractEventLoop, call: Callable[[*A], None], *args: *A
) -> None:
    try:
        _ = loop.call_soon_threadsafe(call, *args)
    except RuntimeError:
        pass


def _listened(future: asyncio.Future[None]) -> None:
    if not future.done():
        future.set_result(None)
