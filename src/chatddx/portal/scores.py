from datetime import datetime
from typing import NamedTuple
from uuid import UUID

from fastapi import APIRouter, Request, Response
from pydantic import JsonValue

from chatddx import settings
from chatddx.bench import Bench, NotFound
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Expectation, Scorer, Scoring
from chatddx.factors.trial import Trial
from chatddx.ledger.record import ItemKey
from chatddx.ledger.run import RunStarted
from chatddx.ledger.score import ScoreItem
from chatddx.scorers.answer import read
from chatddx.scorers.scorer import Mark, Replayed, Verdicts, explain_view
from chatddx.scorers.shipped import function, unit_of

from .judged import judged, verdicts_of
from .pages import BenchDep, page
from .titles import display_case

router = APIRouter()


class Segment(NamedTuple):
    text: str
    marked: bool


class Repeat(NamedTuple):
    run: UUID
    at: datetime
    replicate: int
    href: str | None
    value: float | None
    elsewhere: bool


@router.get("/scores/{score}/{case}/{replicate}/{view}")
def scored(
    request: Request, bench: BenchDep, score: UUID, case: str, replicate: int, view: int
) -> Response:
    try:
        held = bench.store.score(score)
    except LookupError:
        raise NotFound(f"no score {score} of yours") from None
    run = bench.run(held.started.run)
    scoring = resolve(bench.store.get, held.started.scoring, Scoring)
    scorer = resolve(bench.store.get, scoring.scorer, Scorer)
    item = next(
        (
            i
            for i in held.items
            if i.key.case == case and i.key.replicate == replicate and i.view == view
        ),
        None,
    )
    if item is None or view >= len(scorer.views):
        raise NotFound(
            f"score {score} has no item for case {case}, replicate {replicate}, "
            + f"view {view}"
        )
    trial = resolve(bench.store.get, run.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    ran = next(
        i
        for i in bench.store.run(run.run).items
        if i.key.case == case and i.key.replicate == replicate
    )
    answer = read(skeleton, ran.calls[-1].response)
    data = _expected(bench, scoring, case)
    shown = scorer.views[view]
    verdicts = (
        None
        if shown.judge is None
        else verdicts_of(bench, shown.judge, item.judge_calls)
    )
    replayed, unreplayed = _replayed(
        scorer, view, answer.value, data, held.started.scorer_version, verdicts
    )
    judging = (
        None
        if shown.judge is None
        else judged(
            bench,
            scoring,
            shown,
            shown.judge,
            item.judge_calls,
            answer.value,
            data,
            () if replayed is None else replayed.explained.picks,
        )
    )
    labels = bench.labels(scoring.scorer)
    repeats = _repeats(bench, run, trial, skeleton, case, replicate, view, scoring)
    return page(
        request,
        "score.html",
        person=bench.person,
        score=held.started,
        run=run.run,
        case=case,
        title=display_case(bench.titled_case(case)),
        scorer=bench.title(scoring.scorer),
        view=shown,
        judging=judging,
        at=view,
        label=labels[view] if view < len(labels) else str(view),
        unit=unit_of(scorer, view),
        item=item,
        answer=answer,
        data=data,
        replayed=replayed,
        unreplayed=unreplayed,
        agrees=replayed is not None
        and replayed.explained.scored == (item.value, item.detail),
        segments=None if replayed is None else _segmented(replayed),
        siblings=_siblings(held.items, case, view),
        replicate=replicate,
        seed=None if skeleton.greedy else trial.seeds[replicate],
        repeats=repeats[: settings.ROWS_PER_PAGE],
        unshown=max(0, len(repeats) - settings.ROWS_PER_PAGE),
    )


def _expected(bench: BenchDep, scoring: Scoring, case: str) -> JsonValue | None:
    for ref in scoring.expectations:
        expectation = resolve(bench.store.get, ref, Expectation)
        if expectation.case == case:
            return expectation.data
    return None


def _replayed(
    scorer: Scorer,
    view: int,
    answer: JsonValue | None,
    data: JsonValue | None,
    version: int,
    verdicts: Verdicts | None,
) -> tuple[Replayed | None, str | None]:
    if verdicts == []:
        return None, "unasked"
    if data is None:
        return None, "unexpected"
    try:
        metrics = function(scorer)
    except LookupError as e:
        return None, str(e)
    if metrics.version != version:
        return None, f"scored by version {version}, the code is at {metrics.version}"
    return explain_view(scorer, metrics, view, answer, data, verdicts), None


def _segmented(replayed: Replayed) -> list[list[Segment]] | None:
    texts = replayed.explained.texts
    if texts is None:
        return None
    return [
        _segments(text, [m for m in replayed.explained.marks if m.item == i])
        for i, text in enumerate(texts)
    ]


def _segments(text: str, marks: list[Mark]) -> list[Segment]:
    found: list[Segment] = []
    at = 0
    for mark in sorted(marks, key=lambda m: m.start):
        start = max(mark.start, at)
        if start > at:
            found.append(Segment(text[at:start], False))
        if mark.end > start:
            found.append(Segment(text[start : mark.end], True))
        at = max(at, mark.end)
    if at < len(text):
        found.append(Segment(text[at:], False))
    return found


def _siblings(items: tuple[ScoreItem, ...], case: str, view: int) -> list[int]:
    return sorted(
        i.key.replicate for i in items if i.key.case == case and i.view == view
    )


# Policy: the person's own runs only, newest first, and each repeat under the same scorer,
# its own scoring's score first, so that a value apart from this one is the run's rather
# than another expectation's unless it says so.
def _repeats(
    bench: Bench,
    run: RunStarted,
    trial: Trial,
    skeleton: Skeleton,
    case: str,
    replicate: int,
    view: int,
    scoring: Scoring,
) -> list[Repeat]:
    alike = trial.single(skeleton, case, replicate).digest
    found: list[Repeat] = []
    for other in sorted(bench.runs(reaching=case), key=lambda r: r.at, reverse=True):
        held = resolve(bench.store.get, other.trial, Trial)
        if held.skeleton != trial.skeleton or case not in held.cases:
            continue
        for at in range(len(held.seeds)):
            if (other.run, at) == (run.run, replicate):
                continue
            if held.single(skeleton, case, at).digest == alike:
                found.append(_repeat(bench, other, case, at, view, scoring))
    return found


def _repeat(
    bench: Bench,
    run: RunStarted,
    case: str,
    replicate: int,
    view: int,
    scoring: Scoring,
) -> Repeat:
    key = ItemKey(case=case, replicate=replicate)
    scored: list[tuple[bool, UUID, ScoreItem]] = []
    for started in bench.store.scores_of(run.run):
        under = resolve(bench.store.get, started.scoring, Scoring)
        if under.scorer != scoring.scorer:
            continue
        for item in bench.store.score(started.score).items:
            if item.key == key and item.view == view:
                scored.append((started.scoring != scoring.digest, started.score, item))
    if not scored:
        return Repeat(run.run, run.at, replicate, None, None, False)
    elsewhere, score, item = min(scored, key=lambda s: s[0])
    href = f"/scores/{score}/{case}/{replicate}/{view}"
    return Repeat(run.run, run.at, replicate, href, item.value, elsewhere)
