from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from chatddx.store import Queue

from . import schemas
from .events import graded_of, scoring_of
from .people import BenchDep
from .state import no_store

router = APIRouter(tags=["scores"])


@router.post(
    "/runs/{run}/scores",
    status_code=202,
    responses={
        202: {
            "description": "The scorers the run is to be scored by, queued: the "
            + "worker scores it whoever listens, and its events are at "
            + "`/api/runs/{run}/events`."
        },
        409: {"description": "Something is queued or under way for the run already"},
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
    endpoint = "" if started.endpoint is None else started.endpoint.name
    _ = Queue(bench.conn).put(
        bench.person.id, run, endpoint, 0, True, [s.scorer for s in said.scorers]
    )
    response.headers["Location"] = request.app.url_path_for("scores", run=str(run))
    return said


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


@router.get("/runs/{run}/scores/{score}/items", dependencies=[Depends(no_store)])
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
