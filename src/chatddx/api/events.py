from pydantic import BaseModel

from chatddx import bench as benches
from chatddx.bench import Bench, ScorerStarted, ScoringEvent, outcome, usage
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Scorer
from chatddx.ledger import CanaryCall, RunItem
from chatddx.runner.run import (
    CanaryEnded,
    Event,
    ItemEnded,
    ItemStarted,
    Noted,
    Streamed,
    ToolRan,
)
from chatddx.runner.score import ItemScored, JudgeAnswered, JudgeAsked
from chatddx.scorers.aggregate import mean

from . import schemas

type Named = tuple[str, BaseModel]


def sse(name: str, data: BaseModel, id: int | None = None) -> str:
    said = f"event: {name}\ndata: {data.model_dump_json()}\n\n"
    return said if id is None else f"id: {id}\n{said}"


def item_of(skeleton: Skeleton, item: RunItem) -> schemas.Item:
    prompt, completion = usage(item)
    return schemas.Item(
        case=item.key.case,
        replicate=item.key.replicate,
        outcome=outcome(skeleton, item)[0],
        prompt_tokens=prompt,
        completion_tokens=completion,
    )


def graded_of(graded: benches.Graded) -> schemas.Graded:
    views = range(len(graded.scorer.views))
    scored = () if graded.score is None else graded.score.items
    values = [
        [s.value for s in scored if s.view == view and s.value is not None]
        for view in views
    ]
    started = None if graded.score is None else graded.score.started
    return schemas.Graded(
        scorer=graded.scorer.digest,
        name=graded.name,
        score=None if started is None else started.score,
        scoring=None if started is None else started.scoring,
        at=None if started is None else started.at,
        finished=graded.score is not None and graded.score.finished is not None,
        labels=[graded.label(view) for view in views],
        means=[mean(v) if v else None for v in values],
        items=[
            schemas.ScoredItem(
                case=s.key.case, replicate=s.key.replicate, view=s.view, value=s.value
            )
            for s in scored
        ],
        refused=graded.refused,
    )


def event_of(skeleton: Skeleton, event: Event) -> Named:
    match event:
        case ItemStarted(key=key, seed=seed):
            return "item.started", schemas.ItemStartedData(
                case=key.case, replicate=key.replicate, seed=seed
            )
        case Streamed(key=key, delta=delta):
            return "item.delta", schemas.ItemDeltaData(
                case=key.case,
                replicate=key.replicate,
                kind=delta.kind,
                text=delta.text,
                tokens=delta.tokens,
            )
        case ToolRan(key=key, run=run):
            return "item.tool", schemas.ItemToolData(
                case=key.case, replicate=key.replicate, tool=run.model_dump(mode="json")
            )
        case ItemEnded(item=item):
            return "item.ended", schemas.ItemEndedData(
                **item_of(skeleton, item).model_dump(),
                why=outcome(skeleton, item)[1],
            )
        case CanaryEnded(call=call):
            return canary_of(call)
        case Noted(finding=finding):
            return "run.noted", schemas.Finding.of(finding)


def canary_of(call: CanaryCall) -> Named:
    return "canary.ended", schemas.CanaryEndedData(
        phase=call.phase, canary=call.canary, call=call.call.model_dump(mode="json")
    )


def scoring_event_of(bench: Bench, event: ScoringEvent) -> Named:
    match event:
        case ScorerStarted(scorer=scorer, name=name, score=score):
            labels = bench.labels(scorer)
            views = range(len(resolve(bench.get, scorer, Scorer).views))
            return "score.started", schemas.ScoreStartedData(
                scorer=scorer,
                name=name,
                score=score,
                labels=[labels.get(view, f"view {view}") for view in views],
            )
        case ItemScored(item=item):
            return "score.item", schemas.ScoreItemData(
                score=item.score,
                case=item.key.case,
                replicate=item.key.replicate,
                view=item.view,
                value=item.value,
                detail=item.detail,
            )
        case JudgeAsked(key=key):
            return "judge.asked", schemas.JudgeAskedData(
                case=key.case,
                replicate=key.replicate,
                scorer=event.scorer,
                view=event.view,
                judge=event.judge,
                seed_index=event.seed_index,
            )
        case Streamed(key=key, delta=delta):
            return "judge.delta", schemas.JudgeDeltaData(
                case=key.case,
                replicate=key.replicate,
                kind=delta.kind,
                text=delta.text,
                tokens=delta.tokens,
            )
        case JudgeAnswered(key=key, call=judged):
            return "judge.answered", schemas.JudgeAnsweredData(
                case=key.case,
                replicate=key.replicate,
                view=event.view,
                judge=judged.judge,
                seed_index=judged.seed_index,
                verdict=event.verdict,
                call=judged.call.model_dump(mode="json"),
            )
        case Noted(finding=finding):
            return "score.noted", schemas.Finding.of(finding)
