from collections.abc import AsyncIterator
from uuid import UUID

from fastapi.concurrency import run_in_threadpool

from chatddx.bench import Bench
from chatddx.catalog.language import language_of
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Scoring
from chatddx.factors.trial import Trial
from chatddx.identity import Person
from chatddx.ledger import (
    CanaryCall,
    Record,
    RunFinished,
    RunItem,
    RunStarted,
    ScoreFinished,
    ScoreItem,
    ScoreStarted,
    check_run,
)
from chatddx.store import Job, Queue
from chatddx.store.notify import Events, JobChanged, Said

from . import schemas
from .events import (
    Named,
    canary_of,
    graded_of,
    item_ended_of,
    item_started_of,
    score_item_of,
    score_started_of,
    sse,
    started_of,
    tool_of,
)
from .listening import Heard, Lagged
from .state import AppState

# Comment lines, which event readers skip, keep a proxy from cutting a quiet stream.
KEEP_ALIVE = 15.0

type _Key = tuple[str, int]


class Telling:
    def __init__(self, bench: Bench, run: UUID, after: int) -> None:
        started = bench.run(run)
        canaries = [] if started.canaries is None else [started.canaries]
        self._bench: Bench = bench
        self._started: RunStarted = started
        self._registry: Registry = bench.store.load([started.trial, *canaries])
        self._trial: Trial = resolve(self._registry.get, started.trial, Trial)
        self._skeleton: Skeleton = resolve(
            self._registry.get, self._trial.skeleton, Skeleton
        )
        self.last: int = after
        self._begun: set[_Key] = set()
        self._tools: dict[_Key, int] = {}
        self._ended: set[_Key] = set()
        self._scored: bool = False

    @property
    def run(self) -> UUID:
        return self._started.run

    # A row's events end with the one that carries its id.
    def rows(self) -> list[str]:
        told: list[str] = []
        for seq, record in self._bench.store.rows_of(self.run, self.last):
            said = self._row(record)
            told.extend(sse(name, data) for name, data in said[:-1])
            if said:
                told.append(sse(*said[-1], seq))
            self.last = seq
        return told

    def said(self, said: Said) -> list[str]:
        told: list[Named] = []
        for name, value in said:
            model = schemas.EVENTS.get(name)
            if model is None:
                continue
            data = model.model_validate(value)
            match data:
                case schemas.ItemStartedData():
                    at = (data.case, data.replicate)
                    if at in self._ended:
                        continue
                    self._begun.add(at)
                case schemas.ItemDeltaData() | schemas.ItemToolData():
                    at = (data.case, data.replicate)
                    if at in self._ended:
                        continue
                    told.extend(self._begin(at))
                    if isinstance(data, schemas.ItemToolData):
                        self._tools[at] = self._tools.get(at, 0) + 1
                case schemas.RunScoredData():
                    self._scored = True
                case _:
                    pass
            told.append((name, data))
        return [sse(name, data) for name, data in told]

    def tail(self, job: Job | None) -> list[str]:
        told: list[Named] = []
        if not self._scored and (graded := self._bench.scores_of(self._started)):
            scores = [graded_of(g) for g in graded]
            told.append(("run.scored", schemas.RunScoredData(scores=scores)))
        if job is not None and job.status == "failed":
            detail = f"job {job.id} for run {self.run} failed: {job.why}"
            told.append(("error", schemas.ErrorData(detail=detail)))
        halted = None if job is None else job.halt
        told.append(("done", schemas.DoneData(halted=halted)))
        return [sse(name, data) for name, data in told]

    def _row(self, record: Record) -> list[Named]:
        match record:
            case RunStarted():
                language = language_of(self._bench.rows, self._trial.skeleton)
                data = started_of(record, self._trial, self._skeleton, language)
                return [("run.started", data)]
            case CanaryCall():
                return [canary_of(record)]
            case RunItem(key=key):
                at = (key.case, key.replicate)
                tools = [t for turn in record.turns for t in turn.tools]
                told = self._begin(at)
                told.extend(tool_of(*at, t) for t in tools[self._tools.pop(at, 0) :])
                told.append(item_ended_of(self._skeleton, record))
                self._ended.add(at)
                return told
            case RunFinished(findings=noted):
                found = check_run(self._bench.store.run(self.run), self._registry)
                findings = [schemas.Finding.of(f) for f in found]
                return [
                    *(("run.noted", schemas.Finding.of(f)) for f in noted),
                    ("run.finished", schemas.RunFinishedData(findings=findings)),
                ]
            case ScoreStarted():
                self._scored = False
                scorer = resolve(self._bench.store.get, record.scoring, Scoring).scorer
                return [score_started_of(self._bench, scorer, record.score)]
            case ScoreItem():
                self._scored = False
                return [score_item_of(record)]
            case ScoreFinished(findings=noted):
                self._scored = False
                return [("score.noted", schemas.Finding.of(f)) for f in noted]
            case _:
                return []

    def _begin(self, at: _Key) -> list[Named]:
        if at in self._begun:
            return []
        self._begun.add(at)
        return [item_started_of(*at, self._trial.seeds[at[1]])]


# It listens before it reads, so that no row lands unheard in between.
async def told(
    held: AppState, person: Person, run: UUID, after: int
) -> AsyncIterator[str]:
    conn = await run_in_threadpool(held.connect)
    try:
        bench = Bench(conn, person, held.inventory)
        queue = Queue(conn)
        async with held.listener.heard(run) as hearing:
            telling = await run_in_threadpool(Telling, bench, run, after)
            for text in await run_in_threadpool(telling.rows):
                yield text
            under_way = await run_in_threadpool(queue.open, run) is not None
            while under_way:
                try:
                    heard = await hearing.next(KEEP_ALIVE)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    under_way = await run_in_threadpool(queue.open, run) is not None
                    continue
                for text in await _heard(telling, heard):
                    yield text
                if any(isinstance(h, JobChanged | Lagged) for h in heard):
                    under_way = await run_in_threadpool(queue.open, run) is not None
            for text in await run_in_threadpool(telling.rows):
                yield text
            placed = (await run_in_threadpool(queue.placed, [run])).get(run)
            job = None if placed is None else placed.job
            for text in await run_in_threadpool(telling.tail, job):
                yield text
    finally:
        conn.close()


async def _heard(telling: Telling, heard: list[Heard]) -> list[str]:
    told: list[str] = []
    read = False
    for h in heard:
        if isinstance(h, Events):
            told.extend(telling.said(h.said))
            read = False
        elif not isinstance(h, JobChanged) and not read:
            told.extend(await run_in_threadpool(telling.rows))
            read = True
    return told
