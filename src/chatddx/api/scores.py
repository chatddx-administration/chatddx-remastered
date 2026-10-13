from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from . import schemas
from .events import graded_of
from .people import BenchDep

router = APIRouter(tags=["scores"])


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
