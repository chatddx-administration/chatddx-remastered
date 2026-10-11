import asyncio
import logging
import threading
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from chatddx.bench import Bench, Family, outcome
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.identity import Person
from chatddx.ledger import RunStarted, check_run
from chatddx.runner.run import Running

from . import schemas
from .events import Named, event_of, graded_of, item_of, sse
from .people import BenchDep
from .state import AppState, state
from .threads import refused

STREAM = "text/event-stream"
# How often a request waiting for its run asks whether the client is still there.
HEARD = 0.5

log = logging.getLogger(__name__)
router = APIRouter(tags=["runs"])

type Put = Callable[[Named | None], None]


@dataclass(frozen=True)
class _Started:
    bench: Bench
    running: Running
    skeleton: Skeleton
    said: schemas.RunStartedData


def streamed(accept: str | None) -> bool:
    types = [] if accept is None else accept.split(",")
    return any(t.split(";")[0].strip() == STREAM for t in types)


def _families(bench: Bench, given: schemas.NewRun) -> list[Family]:
    login = bench.person.login
    if given.tags is not None:
        tagged = bench.families(given.tags)
        if not tagged:
            raise HTTPException(
                422, f"no case tagged {' or '.join(given.tags)} for {login}"
            )
        return tagged
    seen = {f.id: f for f in bench.families()}
    wanted = list(dict.fromkeys(given.families or ()))
    if not wanted:
        raise HTTPException(422, "a run takes at least one case")
    if missing := [f for f in wanted if f not in seen]:
        raise HTTPException(422, f"no case {missing[0]} for {login}")
    return [seen[f] for f in wanted]


# A run started on a connection of its own, which its thread closes when it ends.
def _start(held: AppState, person: Person, given: schemas.NewRun) -> _Started:
    conn = held.connect()
    try:
        bench = Bench(conn, person, held.inventory, held.facts)
        # What the body names and the person doesn't see is unprocessable, not missing.
        try:
            with refused():
                variation = bench.variation(given.configuration, given.parts.given())
                skeleton = bench.skeleton(variation)
            _ = bench.endpoint(given.endpoint)
        except LookupError as e:
            raise HTTPException(422, str(e)) from None
        cases = [f.case for f in _families(bench, given)]
        seed = suggest_seeds(1)[0] if given.seed is None else given.seed
        with refused():
            running = bench.start(variation, given.endpoint, cases, seed)
    except BaseException:
        conn.close()
        raise
    trial = resolve(bench.get, running.started.trial, Trial)
    said = schemas.RunStartedData(
        run=running.run,
        trial=trial.digest,
        skeleton=trial.skeleton,
        endpoint=given.endpoint,
        cases=list(trial.cases),
        seed=seed,
        greedy=skeleton.greedy,
    )
    return _Started(bench, running, skeleton, said)


# Sends the run, then finishes and scores it, whether or not the request that started
# it is still listening; a halt ends the sending early.
def _send(started: _Started, score: bool, put: Put) -> None:
    bench, running = started.bench, started.running
    try:
        try:
            running.send(lambda event: put(event_of(started.skeleton, event)))
        except KeyboardInterrupt:
            # A call was stopped, as a runaway answer is, and the run ends with it.
            pass
        findings = [schemas.Finding.of(f) for f in running.finish()]
        put(("run.finished", schemas.RunFinishedData(findings=findings)))
        if score:
            graded = [graded_of(g) for g in bench.score(running.started)]
            put(("run.scored", schemas.RunScoredData(scores=graded)))
    except Exception as e:
        log.exception("run %s failed", running.run)
        put(("error", schemas.ErrorData(detail=f"run {running.run} failed: {e}")))
    finally:
        bench.conn.close()
        put(None)


async def _stream(
    running: Running, events: asyncio.Queue[Named | None]
) -> AsyncIterator[str]:
    try:
        while (named := await events.get()) is not None:
            yield sse(*named)
    finally:
        running.halt()


# The events up to the run's end, and why it failed if it did.
async def _drained(events: asyncio.Queue[Named | None]) -> str | None:
    failed: str | None = None
    while (named := await events.get()) is not None:
        if isinstance(named[1], schemas.ErrorData):
            failed = named[1].detail
    return failed


# Waits for the run to end, halting it if the client goes away meanwhile.
async def _ended(
    request: Request, running: Running, events: asyncio.Queue[Named | None]
) -> str | None:
    ending = asyncio.create_task(_drained(events))
    halted = False
    while not ending.done():
        _ = await asyncio.wait([ending], timeout=HEARD)
        if not (ending.done() or halted) and await request.is_disconnected():
            running.halt()
            halted = True
    return ending.result()


@router.post(
    "/runs",
    status_code=201,
    response_model=schemas.RunDetail,
    responses={
        201: {
            "description": "The run, once it is finished and scored; or, when "
            + f"`Accept` asks for `{STREAM}`, its events as they come: "
            + ", ".join(f"`{name}`" for name in schemas.EVENTS)
            + ", each with its data as JSON.",
            "content": {STREAM: {"schema": {"type": "string"}}},
        }
    },
)
async def start(
    request: Request,
    response: Response,
    bench: BenchDep,
    given: schemas.NewRun,
    accept: Annotated[str | None, Header()] = None,
) -> schemas.RunDetail | StreamingResponse:
    started = await run_in_threadpool(_start, state(request), bench.person, given)
    loop = asyncio.get_running_loop()
    events: asyncio.Queue[Named | None] = asyncio.Queue()
    events.put_nowait(("run.started", started.said))

    def put(named: Named | None) -> None:
        try:
            _ = loop.call_soon_threadsafe(events.put_nowait, named)
        except RuntimeError:
            pass

    made = started.running.run
    threading.Thread(
        target=_send, args=(started, given.score, put), name=f"chatddx-run-{made}"
    ).start()
    location = request.app.url_path_for("run", run=str(made))
    if streamed(accept):
        return StreamingResponse(
            _stream(started.running, events),
            status_code=201,
            media_type=STREAM,
            headers={
                "Location": location,
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    failed = await _ended(request, started.running, events)
    if failed is not None:
        raise HTTPException(500, failed)
    response.headers["Location"] = location
    return await run_in_threadpool(detail, bench, made)


def run_of(bench: Bench, started: RunStarted, finished: bool) -> schemas.Run:
    trial = resolve(bench.get, started.trial, Trial)
    return schemas.Run(
        id=started.run,
        at=started.at,
        trial=trial.digest,
        skeleton=trial.skeleton,
        engine=trial.engine,
        endpoint=None if started.endpoint is None else started.endpoint.name,
        cases=list(trial.cases),
        seeds=list(trial.seeds),
        described=bench.described(started),
        finished=finished,
    )


def detail(bench: Bench, run: UUID) -> schemas.RunDetail:
    started = bench.run_by_id(run)
    whole = bench.store.run(run)
    roots = [started.trial, *([] if started.canaries is None else [started.canaries])]
    registry = bench.store.load(roots)
    trial = resolve(registry.get, started.trial, Trial)
    skeleton = resolve(registry.get, trial.skeleton, Skeleton)
    finished = whole.finished
    noted = () if finished is None else finished.findings
    return schemas.RunDetail(
        **run_of(bench, started, finished is not None).model_dump(),
        rig=schemas.Rig(**started.rig.model_dump()),
        finished_at=None if finished is None else finished.at,
        noted=[schemas.Finding.of(f) for f in noted],
        findings=[schemas.Finding.of(f) for f in check_run(whole, registry)],
        items=[item_of(skeleton, item) for item in whole.items],
        scores=[graded_of(g) for g in bench.scores_of(run)],
    )


@router.get("/runs")
def runs(
    bench: BenchDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    trial: Annotated[str | None, Query(description="a trial's digest")] = None,
    reaching: Annotated[
        str | None, Query(description="a digest the run's trial is built on")
    ] = None,
    scored_by: Annotated[str | None, Query(description="a scorer's digest")] = None,
) -> list[schemas.Run]:
    found = bench.runs()
    if trial is not None:
        found = [r for r in found if r.trial == trial]
    for kept in (
        None if reaching is None else bench.reaching(reaching),
        None if scored_by is None else bench.scored_by(scored_by),
    ):
        if kept is not None:
            ids = {r.run for r in kept}
            found = [r for r in found if r.run in ids]
    page = found[offset : offset + limit]
    finished = bench.store.finished([r.run for r in page])
    return [run_of(bench, r, r.run in finished) for r in page]


@router.get("/runs/{run}")
def run(bench: BenchDep, run: UUID) -> schemas.RunDetail:
    return detail(bench, run)


# Case-derived: the one place the API gives what a run's calls answered, besides the
# stream.
@router.get("/runs/{run}/items")
def items(bench: BenchDep, run: UUID) -> list[schemas.ItemDetail]:
    started = bench.run_by_id(run)
    trial = resolve(bench.get, started.trial, Trial)
    skeleton = resolve(bench.get, trial.skeleton, Skeleton)
    return [
        schemas.ItemDetail(
            **item_of(skeleton, item).model_dump(),
            why=outcome(skeleton, item)[1],
            vignette=item.vignette.model_dump(mode="json"),
            call=item.call.model_dump(mode="json"),
            turns=[t.model_dump(mode="json") for t in item.turns],
        )
        for item in bench.store.run(run).items
    ]


@router.get("/runs/{run}/rendered-again")
def rendered_again(bench: BenchDep, run: UUID) -> list[schemas.RenderedAgain]:
    _ = bench.run_by_id(run)
    return [
        schemas.RenderedAgain(
            case=key.case, replicate=key.replicate, same=why is None, why=why
        )
        for key, why in bench.rendered_again(bench.store.run(run)).items()
    ]
