import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Literal
from uuid import UUID, uuid4

import psycopg

from chatddx import settings
from chatddx.bench import Bench, ScoreHalt
from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.runner.run import Running
from chatddx.store import Job, People, Queue
from chatddx.store.store import Connection

log = logging.getLogger(__name__)

PAUSED = "paused"
LEFT = "its worker stopped"


@dataclass
class _Held:
    job: Job
    scoring: ScoreHalt = field(default_factory=ScoreHalt)
    running: Running | None = None
    halted: bool = False
    left: str | None = None
    guard: threading.Lock = field(default_factory=threading.Lock)

    def sending(self, running: Running) -> None:
        with self.guard:
            self.running = running
            if self.halted:
                running.halt()
            elif self.left is not None:
                running.stop()

    def halt(self) -> None:
        with self.guard:
            self.halted = True
            if self.running is not None:
                self.running.halt()
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
        facts: Facts,
        beat: timedelta = settings.WORKER_BEAT,
        lost: timedelta = settings.WORKER_LOST,
    ) -> None:
        self.id: UUID = uuid4()
        self._conninfo: str = conninfo
        self._inventory: Inventory = inventory
        self._facts: Facts = facts
        self._beat_every: float = beat.total_seconds()
        self._lost: timedelta = lost
        self._guard: threading.Lock = threading.Lock()
        self._held: dict[int, _Held] = {}

    def serve(self, stopping: threading.Event) -> None:
        max_jobs = {name: e.max_jobs for name, e in self._inventory.endpoints.items()}
        with self._connect() as conn:
            queue = Queue(conn)
            queue.enlist(self.id)
            while True:
                leaving = stopping.is_set()
                if leaving:
                    for held in self._holding().values():
                        held.leave(LEFT)
                self._beat(queue)
                if leaving:
                    if not self._holding():
                        return
                    time.sleep(self._beat_every)
                    continue
                while (job := queue.claim(self.id, max_jobs, self._lost)) is not None:
                    self._take(job)
                _ = stopping.wait(self._beat_every)

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
            with self._connect() as conn:
                queue = Queue(conn)
                try:
                    went = self._done(conn, held)
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

    def _done(
        self, conn: Connection, held: _Held
    ) -> Literal["finished", "stopped", "queued"]:
        job = held.job
        bench = Bench(conn, People(conn).get(job.owner), self._inventory, self._facts)
        started = bench.run_by_id(job.run)
        if bench.store.run(job.run).finished is None:
            running = bench.resume(job.run)
            held.sending(running)
            running.send()
            if held.left is not None and not held.halted:
                return "queued"
            _ = running.finish()
        if job.score and not held.halted:
            _ = bench.score(started, job.scorers, halt=held.scoring)
        return "stopped" if held.halted else "finished"
