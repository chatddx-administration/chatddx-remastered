from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from . import schemas
from .events import graded_of, scoring_of
from .people import BenchDep
from .state import no_store, refused

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
    started = bench.run(run)
    with refused():
        scorers = bench.queue_scoring(started, given.scorers)
    response.headers["Location"] = request.app.url_path_for("scores", run=str(run))
    return scoring_of(bench, started, scorers)


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
    return [graded_of(g) for g in bench.scores_of(bench.run(run), every)]


@router.get("/runs/{run}/scores/{score}/items", dependencies=[Depends(no_store)])
def items(
    bench: BenchDep,
    run: UUID,
    score: UUID,
    case: Annotated[str | None, Query(description="only this case's items")] = None,
) -> schemas.ScoreItems:
    held = bench.score_of(bench.run(run), score).score
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
            if case is None or i.key.case == case
        ],
        findings=[]
        if finished is None
        else [schemas.Finding.of(f) for f in finished.findings],
    )
