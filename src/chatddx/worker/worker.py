import logging
import select
import socket
import threading
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Literal
from uuid import UUID, uuid4

import psycopg

from chatddx import settings
from chatddx.api import schemas
from chatddx.api.events import graded_of, scoring_of
from chatddx.bench import Bench, Graded
from chatddx.inventory import Inventory, check
from chatddx.ledger import RunStarted
from chatddx.runner import Halt, Running
from chatddx.store import Job, People, Queue, Store
from chatddx.store.notify import WORKERS, listen
from chatddx.store.store import Connection

from .publish import Publisher

log = logging.getLogger(__name__)

PAUSED = "paused"
LEFT = "its worker stopped"


@dataclass
class _Held:
    job: Job
    halting: Halt = field(default_factory=Halt)
    scoring: Halt = field(default_factory=Halt)
    running: Running | None = None
    left: str | None = None
    cut: bool = False
    guard: threading.Lock = field(default_factory=threading.Lock)

    @property
    def halted(self) -> bool:
        return self.halting.is_set()

    def sending(self, running: Running) -> None:
        with self.guard:
            self.running = running
            if self.left is not None:
                running.stop()

    def halt(self) -> None:
        self.halting.set()
        self.scoring.set()

    def cut_short(self) -> None:
        with self.guard:
            self.cut = True
        self.scoring.set()

    def leave(self, why: str) -> None:
        with self.guard:
            if self.left is None:
                self.left = why
            if self.running is not None:
                self.running.stop()


class Worker:
    def __init__(
        self,
        conninfo: str,
        inventory: Inventory,
        beat: timedelta = settings.WORKER_BEAT,
        lost: timedelta = settings.WORKER_LOST,
        deadline: timedelta = settings.WORKER_DEADLINE,
        jobs: int = settings.WORKER_JOBS,
    ) -> None:
        self.id: UUID = uuid4()
        self._conninfo: str = conninfo
        self._inventory: Inventory = inventory
        self._beat_every: float = beat.total_seconds()
        self._lost: timedelta = lost
        self._deadline: float = deadline.total_seconds()
        self._jobs: int = jobs
        self._guard: threading.Lock = threading.Lock()
        self._held: dict[int, _Held] = {}
        self._waking: socket.socket | None = None

    def serve(self, stopping: threading.Event) -> None:
        capacity = {name: e.capacity for name, e in self._inventory.endpoints.items()}
        woken, waking = socket.socketpair()
        waking.setblocking(False)
        with self._guard:
            self._waking = waking
        try:
            with self._connect() as conn:
                for f in check(self._inventory, Store(conn).get):
                    log.log(
                        logging.INFO if f.level == "info" else logging.WARNING,
                        "[world %s] %s: %s: %s",
                        f.level,
                        f.subject,
                        f.code,
                        f.message,
                    )
                queue = Queue(conn)
                queue.enlist(self.id)
                listen(conn, WORKERS)
                deadline: float | None = None
                while True:
                    leaving = stopping.is_set()
                    if leaving and deadline is None:
                        deadline = time.monotonic() + self._deadline
                    if deadline is not None:
                        past = time.monotonic() >= deadline
                        for held in self._holding().values():
                            held.leave(LEFT)
                            if past:
                                held.cut_short()
                    self._beat(queue)
                    if leaving and not self._holding():
                        return
                    if not leaving:
                        while (
                            len(self._holding()) < self._jobs
                            and (job := queue.claim(self.id, capacity, self._lost))
                            is not None
                        ):
                            self._take(job)
                    self._wait(conn, woken, deadline)
        finally:
            with self._guard:
                self._waking = None
            woken.close()
            waking.close()

    def wake(self) -> None:
        with self._guard:
            if self._waking is None:
                return
            try:
                _ = self._waking.send(b"\0")
            except OSError:
                pass

    def _wait(
        self, conn: Connection, woken: socket.socket, deadline: float | None
    ) -> None:
        if list(conn.notifies(timeout=0)):
            return
        timeout = self._beat_every
        if deadline is not None:
            timeout = max(min(timeout, deadline - time.monotonic()), 0.0)
        ready, _, _ = select.select([conn.fileno(), woken], [], [], timeout)
        if woken in ready:
            _ = woken.recv(4096)
        for _ in conn.notifies(timeout=0):
            pass

    def _connect(self) -> Connection:
        return psycopg.connect(self._conninfo, autocommit=True)

    def _holding(self) -> dict[int, _Held]:
        with self._guard:
            return dict(self._held)

    def _beat(self, queue: Queue) -> None:
        holding = self._holding()
        signals = {s.job: s for s in queue.beat(self.id, holding)}
        for id, held in holding.items():
            signal = signals.get(id)
            if signal is None:
                held.leave("another worker took it over")
            elif signal.halt:
                held.halt()
            elif signal.paused:
                held.leave(PAUSED)

    def _take(self, job: Job) -> None:
        held = _Held(job)
        if job.halt:
            held.halt()
        with self._guard:
            self._held[job.id] = held
        threading.Thread(
            target=self._work, args=(held,), name=f"chatddx-job-{job.id}"
        ).start()

    def _work(self, held: _Held) -> None:
        job = held.job
        try:
            with self._connect() as conn, self._connect() as told:
                queue = Queue(conn)
                try:
                    went = self._done(conn, Publisher(told, job.run), held)
                except Exception as e:
                    log.exception("job %s, run %s, failed", job.id, job.run)
                    _ = queue.end(job.id, self.id, "failed", str(e) or type(e).__name__)
                else:
                    if went == "queued":
                        _ = queue.requeue(job.id, self.id, held.left)
                    else:
                        _ = queue.end(job.id, self.id, went)
        except Exception:
            log.exception("job %s, run %s, couldn't be ended", job.id, job.run)
        finally:
            with self._guard:
                del self._held[job.id]
            self.wake()

    def _done(
        self, conn: Connection, publisher: Publisher, held: _Held
    ) -> Literal["finished", "stopped", "queued"]:
        job = held.job
        bench = Bench(conn, People(conn).get(job.owner), self._inventory)
        started = bench.run(job.run)
        try:
            if bench.store.run(job.run).finished is None:
                running = bench.resume(started)
                held.sending(running)
                running.send(publisher.run_event, held.halting)
                if held.left is not None and not held.halted:
                    return "queued"
                _ = running.finish()
            if job.score and not held.halted:
                graded = self._scored(conn, bench, started, publisher, held)
                if held.cut and not held.halted:
                    return "queued"
                latest = {g.scorer.digest: g for g in bench.scores_of(started)}
                told = {**latest, **{g.scorer.digest: g for g in graded}}.values()
                scores = [graded_of(g) for g in sorted(told, key=lambda g: g.name)]
                publisher.put(("run.scored", schemas.RunScoredData(scores=scores)))
        finally:
            publisher.close()
        return "stopped" if held.halted else "finished"

    # Policy: scorer by scorer, so that the job keeps those it finished: queued again, it
    # scores what is left.
    def _scored(
        self,
        conn: Connection,
        bench: Bench,
        started: RunStarted,
        publisher: Publisher,
        held: _Held,
    ) -> list[Graded]:
        job, queue = held.job, Queue(conn)
        left = [
            e.digest
            for e, _, _ in bench.scorers(started)
            if (job.scorers is None or e.digest in job.scorers)
            and e.digest not in job.scored
        ]
        publisher.put(("run.scoring", scoring_of(bench, started, left)))
        graded: list[Graded] = []
        for scorer in left:
            graded.extend(
                bench.score(started, {scorer}, publisher.scoring_event, held.scoring)
            )
            if not held.scoring.is_set():
                _ = queue.scored(job.id, self.id, scorer)
        return graded
