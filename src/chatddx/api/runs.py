from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from chatddx.bench import Bench, Family, Started
from chatddx.catalog import Subject, families
from chatddx.catalog.language import language_of
from chatddx.catalog.read import about as about_of
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Execution, Trial, suggest_seeds
from chatddx.ledger import RunStarted, check_run
from chatddx.runner import Running, outcome, rendered_again as rendered
from chatddx.scorers.answer import read
from chatddx.store import Queue
from chatddx.store.queue import Placed

from . import schemas
from .events import graded_of, item_of, started_of
from .people import BenchDep
from .state import NO_STORE, no_store, state
from .telling import told
from .threads import refused

STREAM = "text/event-stream"
EVENTS = ", ".join(f"`{name}`" for name in schemas.EVENTS)

router = APIRouter(tags=["runs"])


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
    seen = {f.id: f for f in bench.families()}
    for case in wanted:
        family = seen.get(families.family_of(bench.rows, case) or 0)
        if family is None or case not in family.cases:
            raise HTTPException(422, f"no case {case} for {bench.person.login}")
    return wanted


def _seeds(given: schemas.Seeds, replicates: int) -> tuple[int, ...]:
    if given.seeds is not None:
        return tuple(given.seeds)
    return suggest_seeds(given.replicates or replicates)


def _execution(held: Execution, given: schemas.NewRun) -> Execution | None:
    if given.concurrency is None and given.order is None:
        return None
    order = given.order or held.order
    shuffled = held.shuffle_seed if order == held.order else suggest_seeds(1)[0]
    return Execution.model_validate(
        {
            **held.model_dump(),
            "concurrency": given.concurrency or held.concurrency,
            "order": order,
            "shuffle_seed": shuffled if order == "shuffled@1" else None,
        }
    )


def _new(bench: Bench, given: schemas.NewRun) -> Started:
    try:
        with refused():
            variation = bench.variation(
                given.configuration, given.parts.given(), given.head
            )
            at = bench.at(variation, given.endpoint)
    except LookupError as e:
        raise HTTPException(422, str(e)) from None
    cases = _cases(bench, given)
    with refused():
        return bench.start(
            variation,
            at.name,
            cases,
            _seeds(given, 1),
            given.cleanup,
            _execution(at.spec.execution, given),
        )


def _repeated(bench: Bench, run: UUID, given: schemas.NewAgain) -> Running:
    before = bench.run(run)
    trial = resolve(bench.store.get, before.trial, Trial)
    seen = {f.id for f in bench.families()}
    for case in trial.cases:
        if families.family_of(bench.rows, case) not in seen:
            raise HTTPException(422, f"no case {case} for {bench.person.login}")
    with refused():
        return bench.again(before, _seeds(given, len(trial.seeds)))


def _queued(
    request: Request, response: Response, bench: Bench, running: Running, score: bool
) -> schemas.RunStartedData:
    started = running.started
    assert started.endpoint is not None
    trial = resolve(bench.store.get, started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    _ = Queue(bench.conn).put(
        bench.person.id,
        started.run,
        started.endpoint.name,
        started.execution.concurrency,
        score,
    )
    response.headers["Location"] = request.app.url_path_for("run", run=str(started.run))
    language = language_of(bench.rows, trial.skeleton)
    return started_of(started, trial, skeleton, language)


@router.post(
    "/runs",
    status_code=202,
    responses={
        202: {
            "description": "The runs, started and queued, a run per language its cases "
            + "are sent in, `Location` the first's: the worker sends each, finishes "
            + "it and scores it whoever listens, and its events are at "
            + "`/api/runs/{run}/events`."
        }
    },
)
def start(
    request: Request, response: Response, bench: BenchDep, given: schemas.NewRun
) -> schemas.StartedRuns:
    started = _new(bench, given)
    runs = [_queued(request, response, bench, r, given.score) for _, r in started.runs]
    first = str(runs[0].run)
    response.headers["Location"] = request.app.url_path_for("run", run=first)
    return schemas.StartedRuns(
        runs=runs,
        left_out=[
            schemas.LeftOut(language=c.language, cases=c.cases, why=c.refused)
            for c in started.left_out
            if c.language is not None and c.refused is not None
        ],
    )


@router.post(
    "/runs/{run}/again",
    status_code=202,
    responses={
        202: {
            "description": "The run's trial started again with other seeds, as a run "
            + "of its own, named as the run is, and queued: the worker sends it, "
            + "finishes it and scores it whoever listens, and its events are at "
            + "`/api/runs/{run}/events`."
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
    _ = bench.run(run)
    running = _repeated(bench, run, given)
    return _queued(request, response, bench, running, given.score)


@router.post(
    "/runs/{run}/resume",
    status_code=202,
    responses={
        202: {
            "description": "The unfinished run, queued again: the worker sends what it "
            + "lacks, finishes it and scores it whoever listens, and its events are at "
            + "`/api/runs/{run}/events`."
        },
        409: {"description": "Something is queued or under way for the run already"},
    },
)
def resume(
    request: Request,
    response: Response,
    bench: BenchDep,
    run: UUID,
    given: schemas.NewResume,
) -> schemas.RunStartedData:
    started = bench.run(run)
    with refused():
        running = bench.resume(started)
    return _queued(request, response, bench, running, given.score)


@router.get(
    "/runs/{run}/events",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "What the run does, as it does it: the run's rows in the "
            + "ledger in the order they were written, each event of a row with the "
            + "row's number as its id, the last one a row tells holding it; then, "
            + "while a job for the run is queued or under way, what the worker says "
            + "as it happens, without ids, and the rows as they land. The events are "
            + f"{EVENTS}, each with its data as JSON; `done` is the last.",
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
    _ = await run_in_threadpool(bench.run, run)
    return StreamingResponse(
        told(state(request), bench.person, run, last or 0),
        media_type=STREAM,
        headers={**NO_STORE, "X-Accel-Buffering": "no"},
    )


@router.post(
    "/runs/{run}/halt",
    status_code=204,
    responses={409: {"description": "Nothing is queued or under way for the run"}},
)
def halt(bench: BenchDep, run: UUID) -> Response:
    _ = bench.run(run)
    try:
        _ = Queue(bench.conn).halt(run)
    except LookupError as e:
        raise HTTPException(409, str(e)) from None
    return Response(status_code=204)


def job_of(placed: Placed | None) -> schemas.RunJob | None:
    if placed is None:
        return None
    job = placed.job
    return schemas.RunJob(
        status=job.status,
        why=job.why,
        halt=job.halt,
        ahead=placed.ahead,
        queued=job.queued,
        ended=job.ended,
    )


def run_of(
    bench: Bench,
    started: RunStarted,
    finished: bool,
    unscored: list[str] | None = None,
    placed: Placed | None = None,
) -> schemas.Run:
    trial = resolve(bench.store.get, started.trial, Trial)
    about = about_of(bench.rows, Subject(run=started.run))
    ran = None if about.varied is None else bench.rows.edit(about.varied)
    return schemas.Run(
        id=started.run,
        at=started.at,
        trial=trial.digest,
        skeleton=trial.skeleton,
        language=language_of(bench.rows, trial.skeleton),
        started_with=about.started_with,
        engine=trial.engine,
        endpoint=None if started.endpoint is None else started.endpoint.name,
        cases=list(trial.cases),
        seeds=list(trial.seeds),
        described=bench.described(started),
        ran=None
        if ran is None
        else schemas.Ran(configuration=ran.thread, head=ran.id, parts=about.replaced),
        finished=finished,
        unscored=None
        if unscored is None
        else [schemas.Unscored(scorer=s, name=bench.title(s)) for s in unscored],
        job=job_of(placed),
    )


def detail(bench: Bench, run: UUID) -> schemas.RunDetail:
    started = bench.run(run)
    whole = bench.store.run(run)
    roots = [started.trial, *([] if started.canaries is None else [started.canaries])]
    registry = bench.store.load(roots)
    trial = resolve(registry.get, started.trial, Trial)
    skeleton = resolve(registry.get, trial.skeleton, Skeleton)
    finished = whole.finished
    noted = () if finished is None else finished.findings
    placed = Queue(bench.conn).placed([run]).get(run)
    return schemas.RunDetail(
        **run_of(bench, started, finished is not None, placed=placed).model_dump(),
        rig=schemas.Rig(**started.rig.model_dump()),
        finished_at=None if finished is None else finished.at,
        noted=[schemas.Finding.of(f) for f in noted],
        findings=[schemas.Finding.of(f) for f in check_run(whole, registry)],
        items=[item_of(skeleton, item) for item in whole.items],
        scores=[graded_of(g) for g in bench.scores_of(started)],
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
    started_with: Annotated[
        UUID | None,
        Query(
            alias="with",
            description="a run: the runs started with it, itself the first of them",
        ),
    ] = None,
) -> list[schemas.Run]:
    found = bench.runs(
        reaching=reaching, scored_by=scored_by, started_with=started_with
    )
    if trial is not None:
        found = [r for r in found if r.trial == trial]
    left: dict[UUID, list[str]] = {}
    if unscored:
        left = {r.run: scorers for r, scorers in bench.outstanding()}
        found = [r for r in found if r.run in left]
    page = found[offset : offset + limit]
    finished = bench.store.finished([r.run for r in page])
    placed = Queue(bench.conn).placed([r.run for r in page])
    return [
        run_of(bench, r, r.run in finished, left.get(r.run), placed.get(r.run))
        for r in page
    ]


@router.get("/runs/{run}")
def run(bench: BenchDep, run: UUID) -> schemas.RunDetail:
    return detail(bench, run)


@router.get("/runs/{run}/items", dependencies=[Depends(no_store)])
def items(bench: BenchDep, run: UUID) -> list[schemas.ItemDetail]:
    started = bench.run(run)
    trial = resolve(bench.store.get, started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
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
    _ = bench.run(run)
    again = rendered(bench.conn, bench.inventory, bench.store.run(run))
    return [
        schemas.RenderedAgain(
            case=key.case, replicate=key.replicate, same=why is None, why=why
        )
        for key, why in again.items()
    ]
