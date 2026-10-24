from statistics import mean
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from chatddx.bench import Bench, Graded, NotFound, Started, Titled
from chatddx.catalog import Subject
from chatddx.catalog.language import language_of
from chatddx.catalog.read import about as about_of
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.ledger import RunStarted, check_run
from chatddx.runner import Running, outcome, rendered_again as rendered
from chatddx.scorers.answer import read
from chatddx.store import Queue
from chatddx.store.queue import Placed

from . import schemas
from .events import graded_of, item_of, started_of
from .people import BenchDep
from .state import NO_STORE, Refusing, no_store, refused, state
from .telling import told

STREAM = "text/event-stream"
EVENTS = ", ".join(f"`{name}`" for name in schemas.EVENTS)

router = APIRouter(tags=["runs"])


def _cases(bench: Bench, given: schemas.NewRun) -> list[str]:
    if given.cases is not None:
        return list(dict.fromkeys(given.cases))
    if given.tags is None:
        return [bench.family(f).case for f in dict.fromkeys(given.families or ())]
    if tagged := bench.families(given.tags):
        return [f.case for f in tagged]
    raise ValueError(
        f"no case tagged {' or '.join(given.tags)} for {bench.person.login}"
    )


def _seeds(given: schemas.Seeds, replicates: int) -> tuple[int, ...]:
    if given.seeds is not None:
        return tuple(given.seeds)
    return suggest_seeds(given.replicates or replicates)


def _new(bench: Bench, given: schemas.NewRun) -> Started:
    with refused(NotFound):
        variation = bench.variation(
            given.configuration, given.parts.given(), given.head
        )
        at = bench.at(variation, model=given.under)
        return bench.start(
            variation,
            at.name,
            _cases(bench, given),
            _seeds(given, 1),
            given.cleanup,
            at.spec.execution.overlaid(given.concurrency, given.order),
        )


def _queued(
    request: Request, response: Response, bench: Bench, running: Running, score: bool
) -> schemas.RunStartedData:
    started = running.started
    trial = resolve(bench.store.get, started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    _ = bench.queue(running, score)
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
    "/runs/trials",
    status_code=202,
    responses={
        202: {
            "description": "The runs, started and queued, a run per trial's version in "
            + "the order given, `Location` the first's."
        }
    },
)
def start_trials(
    request: Request, response: Response, bench: BenchDep, given: schemas.NewTrialRuns
) -> schemas.StartedRuns:
    with refused():
        started = bench.start_trials(given.trials, given.concurrency, given.order)
    runs = [_queued(request, response, bench, r, given.score) for r in started]
    response.headers["Location"] = request.app.url_path_for("run", run=str(runs[0].run))
    return schemas.StartedRuns(runs=runs, left_out=[])


@router.post(
    "/runs/{run}/again",
    status_code=202,
    responses={
        202: {
            "description": "The run's skeleton started again over its cases under its "
            + "handle, at the handle's latest engine, with other seeds, as a run of its "
            + "own, named as the run is, and queued: the worker sends it, finishes it "
            + "and scores it whoever listens, and its events are at "
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
    before = bench.run(run)
    replicates = len(resolve(bench.store.get, before.trial, Trial).seeds)
    with refused(NotFound):
        running = bench.again(before, _seeds(given, replicates))
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
        raise Refusing(409, e) from None
    return Response(status_code=204)


def _job_of(placed: Placed | None) -> schemas.RunJob | None:
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


def _run_of(
    bench: Bench,
    started: RunStarted,
    finished: bool,
    unscored: list[str] | None = None,
    placed: Placed | None = None,
) -> schemas.Run:
    trial = resolve(bench.store.get, started.trial, Trial)
    about = about_of(bench.rows, Subject(run=started.run))
    ran = None if about.varied is None else bench.rows.edit(about.varied)
    handle, latest = bench.under(trial.engine)
    return schemas.Run(
        id=started.run,
        at=started.at,
        trial=trial.digest,
        skeleton=trial.skeleton,
        language=language_of(bench.rows, trial.skeleton),
        started_with=about.started_with,
        engine=trial.engine,
        endpoint=None if started.endpoint is None else started.endpoint.name,
        model=None if handle is None else handle.name,
        latest=latest,
        cases=list(trial.cases),
        seeds=list(trial.seeds),
        described=bench.described(started),
        titled=_titled(bench.titled(started)),
        ran=None
        if ran is None
        else schemas.Ran(configuration=ran.thread, head=ran.id, parts=about.replaced),
        finished=finished,
        unscored=None
        if unscored is None
        else [schemas.Unscored(scorer=s, name=bench.title(s)) for s in unscored],
        job=_job_of(placed),
    )


def _titled(titled: Titled) -> schemas.Titled:
    return schemas.Titled(
        name=titled.name,
        replaced=[
            schemas.Replaced(part=r.part, title=r.title) for r in titled.replaced
        ],
        at=titled.at,
        case=titled.case,
        cases=titled.cases,
        translated=titled.translated,
        greedy=titled.greedy,
        seeds=list(titled.seeds),
    )


def _detail(bench: Bench, run: UUID) -> schemas.RunDetail:
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
        **_run_of(bench, started, finished is not None, placed=placed).model_dump(),
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
    return _runs_of(bench, found[offset : offset + limit], left)


def _runs_of(
    bench: Bench, started: list[RunStarted], left: dict[UUID, list[str]] | None = None
) -> list[schemas.Run]:
    ids = [r.run for r in started]
    finished = bench.store.finished(ids)
    placed = Queue(bench.conn).placed(ids)
    return [
        _run_of(bench, r, r.run in finished, (left or {}).get(r.run), placed.get(r.run))
        for r in started
    ]


@router.get("/runs/compared")
def compared(
    bench: BenchDep,
    run: Annotated[
        list[UUID], Query(min_length=1, max_length=20, description="the runs, in order")
    ],
) -> schemas.Compared:
    started = [bench.run(r) for r in run]
    trials = [resolve(bench.store.get, s.trial, Trial) for s in started]
    held = [set(t.item_keys) for t in trials]
    shared = [k for k in trials[0].item_keys if all(k in h for h in held)]
    scored = [{g.scorer.digest: g for g in bench.scores_of(s)} for s in started]
    named = {d: g for by in reversed(scored) for d, g in by.items()}
    views: list[schemas.ComparedView] = []
    for digest, graded in sorted(named.items(), key=lambda n: (n[1].name, n[0])):
        for view in range(len(graded.scorer.views)):
            values = [_values(by.get(digest), view, shared) for by in scored]
            found = [[v for v in vs if v is not None] for vs in values]
            views.append(
                schemas.ComparedView(
                    scorer=digest,
                    name=graded.name,
                    view=view,
                    label=graded.label(view),
                    means=[mean(f) if f else None for f in found],
                    values=values,
                )
            )
    return schemas.Compared(
        runs=_runs_of(bench, started),
        views=views,
        items=[schemas.ItemKey(case=c, replicate=r) for c, r in shared],
        apart=[
            schemas.HeldBySome(
                case=case,
                runs=[s.run for s, t in zip(started, trials) if case in t.cases],
            )
            for case in dict.fromkeys(c for t in trials for c in t.cases)
            if not all(case in t.cases for t in trials)
        ],
    )


def _values(
    graded: Graded | None, view: int, shared: list[tuple[str, int]]
) -> list[float | None]:
    score = None if graded is None else graded.score
    held: dict[tuple[str, int], float | None] = {}
    if score is not None:
        held = {
            (i.key.case, i.key.replicate): i.value
            for i in score.items
            if i.view == view
        }
    return [held.get(k) for k in shared]


@router.get("/runs/{run}")
def run(bench: BenchDep, run: UUID) -> schemas.RunDetail:
    return _detail(bench, run)


@router.get("/runs/{run}/items", dependencies=[Depends(no_store)])
def items(
    bench: BenchDep,
    run: UUID,
    case: Annotated[str | None, Query(description="only this case's items")] = None,
) -> list[schemas.ItemDetail]:
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
        if case is None or item.key.case == case
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
