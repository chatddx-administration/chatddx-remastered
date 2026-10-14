import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from chatddx.bench import Bench, Family, outcome
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.identity import Person
from chatddx.ledger import RunStarted, check_run
from chatddx.runner.run import Running
from chatddx.scorers.answer import read

from . import schemas
from .events import Named, canary_of, event_of, graded_of, item_of
from .jobs import Job, ending, followed, replayed, scored, scoring_of
from .people import BenchDep
from .state import NO_STORE, AppState, no_store, state
from .threads import refused

STREAM = "text/event-stream"
EVENTS = ", ".join(f"`{name}`" for name in schemas.EVENTS)

log = logging.getLogger(__name__)
router = APIRouter(tags=["runs"])


@dataclass(frozen=True)
class _Started:
    bench: Bench
    running: Running
    skeleton: Skeleton
    said: schemas.RunStartedData


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


def _cases(bench: Bench, given: schemas.NewRun) -> list[str]:
    if given.cases is None:
        return [f.case for f in _families(bench, given)]
    wanted = list(dict.fromkeys(given.cases))
    if not wanted:
        raise HTTPException(422, "a run takes at least one case")
    seen = {f.id for f in bench.families()}
    for case in wanted:
        family = bench.catalog.family(case)
        if family not in seen or case not in bench.cases(family):
            raise HTTPException(422, f"no case {case} for {bench.person.login}")
    return wanted


type _Starting = Callable[[Bench], tuple[Running, Skeleton, str, int]]


def _opened(held: AppState, person: Person, starting: _Starting) -> _Started:
    conn = held.connect()
    try:
        bench = Bench(conn, person, held.inventory, held.facts)
        running, skeleton, endpoint, seed = starting(bench)
    except BaseException:
        conn.close()
        raise
    trial = resolve(bench.get, running.started.trial, Trial)
    said = schemas.RunStartedData(
        run=running.run,
        trial=trial.digest,
        skeleton=trial.skeleton,
        endpoint=endpoint,
        cases=list(trial.cases),
        seed=seed,
        greedy=skeleton.greedy,
    )
    return _Started(bench, running, skeleton, said)


def _new(given: schemas.NewRun) -> _Starting:
    def starting(bench: Bench) -> tuple[Running, Skeleton, str, int]:
        try:
            with refused():
                variation = bench.variation(
                    given.configuration, given.parts.given(), given.head
                )
                skeleton = bench.skeleton(variation)
            _ = bench.endpoint(given.endpoint)
        except LookupError as e:
            raise HTTPException(422, str(e)) from None
        cases = _cases(bench, given)
        seed = suggest_seeds(1)[0] if given.seed is None else given.seed
        with refused():
            running = bench.start(variation, given.endpoint, cases, seed)
        return running, skeleton, given.endpoint, seed

    return starting


def _repeated(run: UUID, given: schemas.NewAgain) -> _Starting:
    def starting(bench: Bench) -> tuple[Running, Skeleton, str, int]:
        before = bench.run_by_id(run)
        trial = resolve(bench.get, before.trial, Trial)
        seen = {f.id for f in bench.families()}
        for case in trial.cases:
            if bench.catalog.family(case) not in seen:
                raise HTTPException(422, f"no case {case} for {bench.person.login}")
        seed = suggest_seeds(1)[0] if given.seed is None else given.seed
        with refused():
            running = bench.again(before, seed)
        assert before.endpoint is not None
        return (
            running,
            resolve(bench.get, trial.skeleton, Skeleton),
            before.endpoint.name,
            seed,
        )

    return starting


def _launched(
    request: Request, response: Response, started: _Started, score: bool
) -> schemas.RunStartedData:
    made = started.running.run
    job = state(request).jobs.started(made)
    job.running = started.running
    job.put(("run.started", started.said))
    threading.Thread(
        target=_sent, args=(started, score, job), name=f"chatddx-run-{made}"
    ).start()
    response.headers["Location"] = request.app.url_path_for("run", run=str(made))
    return started.said


def _sent(started: _Started, score: bool, job: Job) -> None:
    bench, running = started.bench, started.running
    with ending(job, bench, f"run {running.run}"):
        try:
            running.send(lambda event: job.put(event_of(started.skeleton, event)))
        except KeyboardInterrupt:
            pass
        findings = [schemas.Finding.of(f) for f in running.finish()]
        job.put(("run.finished", schemas.RunFinishedData(findings=findings)))
        if score and not job.halted:
            said = scoring_of(bench, running.started, None)
            job.put(("run.scoring", said))
            scored(bench, running.started, said, job)


@router.post(
    "/runs",
    status_code=202,
    responses={
        202: {
            "description": "The run, started: it is sent, finished and scored whoever "
            + "listens, and its events are at `/api/runs/{run}/events`."
        }
    },
)
def start(
    request: Request, response: Response, bench: BenchDep, given: schemas.NewRun
) -> schemas.RunStartedData:
    started = _opened(state(request), bench.person, _new(given))
    return _launched(request, response, started, given.score)


@router.post(
    "/runs/{run}/again",
    status_code=202,
    responses={
        202: {
            "description": "The run's trial started again with another seed, as a run "
            + "of its own, named as the run is: it is sent, finished and scored whoever "
            + "listens, and its events are at `/api/runs/{run}/events`."
        }
    },
)
def again(
    request: Request,
    response: Response,
    bench: BenchDep,
    run: UUID,
    given: schemas.NewAgain,
) -> schemas.RunStartedData:
    _ = bench.run_by_id(run)
    started = _opened(state(request), bench.person, _repeated(run, given))
    return _launched(request, response, started, given.score)


@router.get(
    "/runs/{run}/events",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "What the run does, as it does it: what is under way for it "
            + "in this process, from its start, then as it comes; else what the ledger "
            + f"holds of it. The events are {EVENTS}, each with an `id` and its data "
            + "as JSON; `done` is the last.",
            "content": {STREAM: {"schema": {"type": "string"}}},
        }
    },
)
async def events(
    request: Request,
    bench: BenchDep,
    run: UUID,
    last: Annotated[
        int | None,
        Header(alias="Last-Event-ID", description="the id of the last event had"),
    ] = None,
) -> StreamingResponse:
    _ = await run_in_threadpool(bench.run_by_id, run)
    job = state(request).jobs.get(run)
    after = last or 0
    if job is None or job.done:
        told = await run_in_threadpool(_told, bench, run)
        body = replayed(told, after)
    else:
        body = followed(job, after)
    return StreamingResponse(
        body,
        media_type=STREAM,
        headers={**NO_STORE, "X-Accel-Buffering": "no"},
    )


@router.post(
    "/runs/{run}/halt",
    status_code=204,
    responses={409: {"description": "Nothing is under way for the run"}},
)
def halt(request: Request, bench: BenchDep, run: UUID) -> Response:
    _ = bench.run_by_id(run)
    job = state(request).jobs.get(run)
    if job is None or job.done:
        raise HTTPException(409, f"run {run} has nothing under way")
    job.halt()
    return Response(status_code=204)


def _told(bench: Bench, run: UUID) -> list[Named]:
    whole = bench.store.run(run)
    started = whole.started
    roots = [started.trial, *([] if started.canaries is None else [started.canaries])]
    registry = bench.store.load(roots)
    trial = resolve(registry.get, started.trial, Trial)
    skeleton = resolve(registry.get, trial.skeleton, Skeleton)
    told: list[Named] = [
        (
            "run.started",
            schemas.RunStartedData(
                run=run,
                trial=trial.digest,
                skeleton=trial.skeleton,
                endpoint=None if started.endpoint is None else started.endpoint.name,
                cases=list(trial.cases),
                seed=trial.seeds[0],
                greedy=skeleton.greedy,
            ),
        ),
        *(canary_of(c) for c in whole.canaries if c.phase == "start"),
    ]
    for item in whole.items:
        key = item.key
        seed = trial.seeds[key.replicate]
        told.append(
            (
                "item.started",
                schemas.ItemStartedData(
                    case=key.case, replicate=key.replicate, seed=seed
                ),
            )
        )
        told.extend(
            (
                "item.tool",
                schemas.ItemToolData(
                    case=key.case,
                    replicate=key.replicate,
                    tool=tool.model_dump(mode="json"),
                ),
            )
            for turn in item.turns
            for tool in turn.tools
        )
        told.append(
            (
                "item.ended",
                schemas.ItemEndedData(
                    **item_of(skeleton, item).model_dump(),
                    why=outcome(skeleton, item)[1],
                ),
            )
        )
    told.extend(canary_of(c) for c in whole.canaries if c.phase == "end")
    if whole.finished is not None:
        told.extend(
            ("run.noted", schemas.Finding.of(f)) for f in whole.finished.findings
        )
        findings = [schemas.Finding.of(f) for f in check_run(whole, registry)]
        told.append(("run.finished", schemas.RunFinishedData(findings=findings)))
        if graded := bench.scores_of(run):
            scores = [graded_of(g) for g in graded]
            told.append(("run.scored", schemas.RunScoredData(scores=scores)))
    told.append(("done", schemas.DoneData(halted=None)))
    return told


def run_of(
    bench: Bench,
    started: RunStarted,
    finished: bool,
    unscored: list[str] | None = None,
) -> schemas.Run:
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
        unscored=None
        if unscored is None
        else [schemas.Unscored(scorer=s, name=bench.scorer_name(s)) for s in unscored],
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
    unscored: Annotated[
        bool,
        Query(description="only the finished runs left to be scored by some scorer"),
    ] = False,
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
    left: dict[UUID, list[str]] = {}
    if unscored:
        left = {r.run: scorers for r, scorers in bench.outstanding()}
        found = [r for r in found if r.run in left]
    page = found[offset : offset + limit]
    finished = bench.store.finished([r.run for r in page])
    return [run_of(bench, r, r.run in finished, left.get(r.run)) for r in page]


@router.get("/runs/{run}")
def run(bench: BenchDep, run: UUID) -> schemas.RunDetail:
    return detail(bench, run)


@router.get("/runs/{run}/items", dependencies=[Depends(no_store)])
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
            answer=schemas.Answer(**read(skeleton, item.calls[-1].response)._asdict()),
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
