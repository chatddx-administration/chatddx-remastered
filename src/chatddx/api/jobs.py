import asyncio
import logging
import threading
from collections.abc import AsyncIterator, Callable, Collection, Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException

from chatddx.bench import Bench, ScoreHalt
from chatddx.ledger import RunStarted
from chatddx.runner.run import Running

from . import schemas
from .events import Named, graded_of, scoring_event_of, sse

log = logging.getLogger(__name__)

# Comment lines, which event readers skip, keep a proxy from cutting a quiet stream.
KEEP_ALIVE = 15.0

# A delta is kept only until what it streams has ended, so a stream joined late replays
# every event but the deltas of the items and judge calls that ended before it.
ENDS = {"item.ended": "item.delta", "judge.answered": "judge.delta"}


@dataclass(frozen=True)
class _Said:
    id: int
    text: str
    delta: tuple[str, object, object] | None


type _Listener = tuple[asyncio.AbstractEventLoop, asyncio.Queue[str | None]]


class Job:
    def __init__(self, run: UUID, ended: Callable[["Job"], None]) -> None:
        self.run: UUID = run
        self.running: Running | None = None
        self.scoring: ScoreHalt = ScoreHalt()
        self._ended: Callable[[Job], None] = ended
        self._guard: threading.Lock = threading.Lock()
        self._said: list[_Said] = []
        self._last: int = 0
        self._listeners: list[_Listener] = []
        self._halted: bool = False
        self._done: bool = False

    @property
    def halted(self) -> bool:
        return self._halted

    @property
    def done(self) -> bool:
        return self._done

    def put(self, named: Named) -> None:
        name, data = named
        case, replicate = getattr(data, "case", None), getattr(data, "replicate", None)
        with self._guard:
            self._last += 1
            said = _Said(
                self._last,
                sse(name, data, self._last),
                None if name not in ENDS.values() else (name, case, replicate),
            )
            if name in ENDS:
                ended = (ENDS[name], case, replicate)
                self._said = [s for s in self._said if s.delta != ended]
            self._said.append(said)
            listeners = list(self._listeners)
        _tell(listeners, said.text)

    def end(self) -> None:
        with self._guard:
            self._done = True
            listeners, self._listeners = self._listeners, []
        self.running = None
        self._ended(self)
        _tell(listeners, None)

    def halt(self) -> None:
        self._halted = True
        if self.running is not None:
            self.running.halt()
        self.scoring.set()

    def listen(self, after: int, listener: _Listener) -> tuple[list[str], bool]:
        with self._guard:
            told = [s.text for s in self._said if s.id > after]
            if not self._done:
                self._listeners.append(listener)
            return told, not self._done

    def leave(self, listener: _Listener) -> None:
        with self._guard:
            if listener in self._listeners:
                self._listeners.remove(listener)


def _tell(listeners: Iterable[_Listener], text: str | None) -> None:
    for loop, queue in listeners:
        try:
            _ = loop.call_soon_threadsafe(queue.put_nowait, text)
        except RuntimeError:
            pass


class Jobs:
    def __init__(self) -> None:
        self._guard: threading.Lock = threading.Lock()
        self._jobs: dict[UUID, Job] = {}

    def get(self, run: UUID) -> Job | None:
        with self._guard:
            return self._jobs.get(run)

    def started(self, run: UUID) -> Job:
        with self._guard:
            held = self._jobs.get(run)
            if held is not None and not held.done:
                raise HTTPException(409, f"run {run} has something under way")
            self._jobs[run] = Job(run, self._drop)
            return self._jobs[run]

    def _drop(self, job: Job) -> None:
        with self._guard:
            if self._jobs.get(job.run) is job:
                del self._jobs[job.run]


async def followed(job: Job, after: int) -> AsyncIterator[str]:
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    listener = (asyncio.get_running_loop(), queue)
    told, live = job.listen(after, listener)
    try:
        for text in told:
            yield text
        while live:
            try:
                text = await asyncio.wait_for(queue.get(), KEEP_ALIVE)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if text is None:
                break
            yield text
    finally:
        job.leave(listener)


# An id past the ledger's numbers is a live job's, which counted its deltas too; the
# stream still ends with `done`, so that the client stops asking.
async def replayed(told: list[Named], after: int) -> AsyncIterator[str]:
    for id, (name, data) in enumerate(told, 1):
        if id > after or name == "done":
            yield sse(name, data, id)


def scoring_of(
    bench: Bench, run: RunStarted, scorers: Collection[str] | None
) -> schemas.ScoringData:
    return schemas.ScoringData(
        scorers=[
            schemas.Unscored(
                scorer=e.digest, name=a.name or bench.catalog.title(e.thread)
            )
            for e, a in bench.scorers_for(run)
            if scorers is None or e.digest in scorers
        ]
    )


def scored(bench: Bench, run: RunStarted, said: schemas.ScoringData, job: Job) -> None:
    graded = bench.score(
        run,
        {s.scorer for s in said.scorers},
        lambda event: job.put(scoring_event_of(bench, event)),
        job.scoring,
    )
    job.put(
        ("run.scored", schemas.RunScoredData(scores=[graded_of(g) for g in graded]))
    )


@contextmanager
def ending(job: Job, bench: Bench, what: str) -> Generator[None]:
    try:
        yield
    except Exception as e:
        log.exception("%s failed", what)
        job.put(("error", schemas.ErrorData(detail=f"{what} failed: {e}")))
    finally:
        bench.conn.close()
        job.put(("done", schemas.DoneData(halted=job.halted)))
        job.end()
