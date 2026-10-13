import threading
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response

from chatddx.bench import Bench
from chatddx.ledger import RunStarted

from . import schemas
from .events import graded_of
from .jobs import Job, ending, scored, scoring_of
from .people import BenchDep
from .state import state

router = APIRouter(tags=["scores"])


@router.post(
    "/runs/{run}/scores",
    status_code=202,
    responses={
        202: {
            "description": "The scorers the run is to be scored by, started: the "
            + "scoring goes on whoever listens, and its events are at "
            + "`/api/runs/{run}/events`."
        },
        409: {"description": "Something is under way for the run already"},
    },
)
def score_now(
    request: Request,
    response: Response,
    bench: BenchDep,
    run: UUID,
    given: schemas.NewScoring,
) -> schemas.ScoringData:
    started = bench.run_by_id(run)
    if run not in bench.store.finished([run]):
        raise HTTPException(422, f"run {run} hasn't finished")
    said = scoring_of(bench, started, given.scorers)
    applying = {s.scorer for s in said.scorers}
    if missing := [s for s in given.scorers or () if s not in applying]:
        raise HTTPException(422, f"scorer {missing[0]} doesn't apply to run {run}")
    if not said.scorers:
        raise HTTPException(422, f"no scorer applies to run {run}")
    held = state(request)
    conn = held.connect()
    try:
        job = held.jobs.started(run)
    except HTTPException:
        conn.close()
        raise
    own = Bench(conn, bench.person, held.inventory, held.facts)
    job.put(("run.scoring", said))
    threading.Thread(
        target=_scoring, args=(own, started, said, job), name=f"chatddx-score-{run}"
    ).start()
    response.headers["Location"] = request.app.url_path_for("scores", run=str(run))
    return said


def _scoring(
    bench: Bench, run: RunStarted, said: schemas.ScoringData, job: Job
) -> None:
    with ending(job, bench, f"scoring run {run.run}"):
        scored(bench, run, said, job)


@router.get("/runs/{run}/scores")
def scores(
    bench: BenchDep,
    run: UUID,
    every: Annotated[
        bool,
        Query(
            alias="all",
            description="every score of the run, newest first, rather than the latest "
            + "under each scorer",
        ),
    ] = False,
) -> list[schemas.Graded]:
    _ = bench.run_by_id(run)
    return [graded_of(g) for g in bench.scores_of(run, every)]


@router.get("/runs/{run}/scores/{score}")
def score(bench: BenchDep, run: UUID, score: UUID) -> schemas.Graded:
    return graded_of(bench.score_of(run, score))


@router.get("/runs/{run}/scores/{score}/items")
def items(bench: BenchDep, run: UUID, score: UUID) -> schemas.ScoreItems:
    held = bench.score_of(run, score).score
    finished = None if held is None else held.finished
    return schemas.ScoreItems(
        items=[
            schemas.ScoreItemDetail(
                case=i.key.case,
                replicate=i.key.replicate,
                view=i.view,
                value=i.value,
                detail=i.detail,
                judge_calls=[c.model_dump(mode="json") for c in i.judge_calls],
            )
            for i in (() if held is None else held.items)
        ],
        findings=[]
        if finished is None
        else [schemas.Finding.of(f) for f in finished.findings],
    )
