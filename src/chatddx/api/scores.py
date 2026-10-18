from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import JsonValue

from chatddx.bench import NotFound
from chatddx.bench.model import PLACEHOLDERS
from chatddx.factors.base import resolve
from chatddx.factors.engine import served_model_name
from chatddx.factors.request import Skeleton, SlotName
from chatddx.factors.scoring import Judge, Scorer, fill_text
from chatddx.factors.select import select
from chatddx.factors.trial import Trial
from chatddx.scorers.answer import read
from chatddx.scorers.scorer import score_view
from chatddx.scorers.shipped import function

from . import schemas
from .events import graded_of, scoring_of
from .people import BenchDep
from .state import no_store, refused
from .threads import component_of

JUDGED: JsonValue = {"reason": "its judge scores it, once the scorer is saved"}

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


@router.post("/scorers/try", dependencies=[Depends(no_store)])
def tried(bench: BenchDep, given: schemas.Trying) -> list[schemas.Tried]:
    with refused():
        scorer = component_of(given.scorer)
    if not isinstance(scorer, Scorer):
        raise HTTPException(422, "only a scorer is tried")
    with refused(LookupError):
        score = function(scorer)
    found: list[schemas.Tried] = []
    for run in given.runs:
        started = bench.run(run)
        trial = resolve(bench.store.get, started.trial, Trial)
        skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
        for item in bench.store.run(run).items:
            if item.key.case != given.case:
                continue
            answer = read(skeleton, item.calls[-1].response).value
            views: list[schemas.TriedView] = []
            for i, view in enumerate(scorer.views):
                if view.judge is not None:
                    views.append(
                        schemas.TriedView(value=None, detail=JUDGED, judged=True)
                    )
                    continue
                said = score_view(scorer, score, i, answer, given.expectation)
                views.append(
                    schemas.TriedView(
                        value=said.value, detail=said.detail, judged=False
                    )
                )
            found.append(
                schemas.Tried(run=run, replicate=item.key.replicate, views=views)
            )
    return found


@router.post("/judges/asked")
def judge_asked(bench: BenchDep, given: schemas.Asking) -> schemas.Asked:
    if bench.rows.kind(given.judge) != "judge":
        raise NotFound(f"no judge {given.judge} in the store")
    judge = resolve(bench.store.get, given.judge, Judge)
    skeleton = resolve(bench.store.get, judge.skeleton, Skeleton)
    with refused():
        picked = select(given.data, given.expectation)
    fills: dict[SlotName, str] = {
        **PLACEHOLDERS,
        "expectation": fill_text(judge.fill, picked),
    }
    request = skeleton.render(
        model=served_model_name(judge.engine, bench.store.get),
        seed=judge.seeds[0],
        fills=fills,
    )
    return schemas.Asked(request=request, picked=picked)
