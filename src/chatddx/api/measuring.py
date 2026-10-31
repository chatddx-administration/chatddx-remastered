from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import JsonValue

from chatddx import settings
from chatddx.bench import Bench
from chatddx.catalog import Subject, read as reading
from chatddx.factors.base import Invalid, resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Scorer, Scoring
from chatddx.factors.select import field as field_of
from chatddx.factors.trial import Trial
from chatddx.scorers.answer import read
from chatddx.scorers.patterns import Pattern
from chatddx.scorers.scorer import Explained, Metrics, explain_view
from chatddx.scorers.shipped import function, unit_of

from . import schemas
from .people import BenchDep
from .state import no_store
from .threads import threads

router = APIRouter(tags=["scores"])


@dataclass(frozen=True)
class _Reading:
    scorer: Scorer
    metrics: Metrics
    views: list[tuple[int, str, str]]


@dataclass
class _Text:
    texts: list[str] | None
    marks: list[schemas.MeasuredMark]
    found: bool | None
    value: float | None
    unit: str
    reason: str | None
    seen: list[schemas.MeasuredSeen] = field(default_factory=list[schemas.MeasuredSeen])


@router.post("/expectations/measured", dependencies=[Depends(no_store)])
def measured(bench: BenchDep, given: schemas.Measuring) -> schemas.Measured:
    """Each view, of the scorers under the schema, that reads the field, scoring each
    answer of the person's runs reaching the case against the data as it is written now,
    the scorers each run was scored by alone; what it found told by what it found, and
    what it missed by what the view picked.

    Costs a read of each such run's items, which hold the answers, and of its scores;
    the scoring itself is local.
    """
    pattern, problem = _pattern(given.data, given.field)
    readings = _Readings(bench, given.expectation_schema, given.field)
    named = _named(bench)
    held: dict[Hashable, _Text] = {}
    answers = 0
    for run in sorted(
        bench.runs(reaching=given.case), key=lambda r: r.at, reverse=True
    ):
        scored = readings.of(run.run)
        if not scored:
            continue
        trial = resolve(bench.store.get, run.trial, Trial)
        skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
        configuration = named(run.run)
        for item in bench.store.run(run.run).items:
            if item.key.case != given.case:
                continue
            answers += 1
            answer = read(skeleton, item.calls[-1].response if item.calls else None)
            for score, at in scored:
                for view, unit, title in at.views:
                    said = explain_view(
                        at.scorer, at.metrics, view, answer.value, given.data
                    ).explained
                    key, text = _told(said, unit)
                    held.setdefault(key, text).seen.append(
                        schemas.MeasuredSeen(
                            run=run.run,
                            at=run.at,
                            replicate=item.key.replicate,
                            configuration=configuration,
                            view=title,
                            href=f"/scores/{score}/{given.case}/{item.key.replicate}/{view}",
                        )
                    )
    texts = sorted(
        held.values(),
        key=lambda t: ({False: 0, None: 1, True: 2}[t.found], -len(t.seen)),
    )
    alternatives = _alternatives(pattern, problem)
    finding = [_finding(alternatives, t) for t in texts]
    return schemas.Measured(
        pattern=pattern,
        problem=problem,
        answers=answers,
        found=sum(len(t.seen) for t in texts if t.found),
        missed=sum(len(t.seen) for t in texts if t.found is False),
        unscored=sum(len(t.seen) for t in texts if t.found is None),
        alternatives=[
            schemas.MeasuredAlternative(
                pattern=a.text,
                found=sum(
                    len(t.seen) for t, f in zip(texts, finding, strict=True) if i in f
                ),
            )
            for i, a in enumerate(alternatives)
        ],
        texts=[
            schemas.MeasuredText(
                texts=t.texts,
                marks=t.marks,
                found=t.found,
                value=t.value,
                unit=t.unit,
                reason=t.reason,
                count=len(t.seen),
                alternatives=f,
                seen=t.seen[: settings.ROWS_PER_PAGE],
            )
            for t, f in zip(texts, finding, strict=True)
        ],
    )


# Policy: what was found is told by the items it was found in alone, so that lists that
# differ only elsewhere are told as one; what was missed by all the view picked, so that
# what the pattern should have found is there to see. A view that picked nothing, for
# want of an answer or a target, scored nothing, whatever its value says.
def _told(said: Explained, unit: str) -> tuple[Hashable, _Text]:
    value = said.scored.value
    detail = said.scored.detail
    reason = (
        str(detail["reason"])
        if isinstance(detail, dict) and "reason" in detail
        else None
    )
    texts = said.texts
    marks = list(said.marks)
    if texts is not None and marks:
        items = sorted({m.item for m in marks})
        texts = [texts[i] for i in items]
        marks = [m._replace(item=items.index(m.item)) for m in marks]
    found = None if texts is None else bool(marks)
    key = (None if texts is None else tuple(texts), tuple(marks), value, unit, reason)
    return key, _Text(
        texts,
        [schemas.MeasuredMark(**m._asdict()) for m in marks],
        found,
        value,
        unit,
        reason,
    )


# Policy: a run's latest score under each scorer alone, so that a run scored again isn't
# told twice.
class _Readings:
    def __init__(self, bench: Bench, schema: str, measured: str) -> None:
        self._bench: Bench = bench
        self._schema: str = schema
        self._measured: str = measured
        self._known: dict[str, _Reading | None] = {}
        self._scorers: dict[str, str] = {}

    def of(self, run: UUID) -> list[tuple[UUID, _Reading]]:
        latest: dict[str, tuple[datetime, UUID]] = {}
        for started in self._bench.store.scores_of(run):
            scorer = self._scorer(started.scoring)
            if scorer not in latest or latest[scorer][0] < started.at:
                latest[scorer] = (started.at, started.score)
        return [
            (score, at)
            for scorer, (_, score) in latest.items()
            if (at := self._reading(scorer)) is not None
        ]

    def _scorer(self, scoring: str) -> str:
        if scoring not in self._scorers:
            held = resolve(self._bench.store.get, scoring, Scoring)
            self._scorers[scoring] = held.scorer
        return self._scorers[scoring]

    def _reading(self, digest: str) -> _Reading | None:
        if digest in self._known:
            return self._known[digest]
        scorer = resolve(self._bench.store.get, digest, Scorer)
        found = None
        if scorer.expectation_schema == self._schema:
            labels = self._bench.labels(digest)
            title = self._bench.title(digest)
            views = [
                (i, unit_of(scorer, i), f"{title} › {labels.get(i, str(i))}")
                for i, v in enumerate(scorer.views)
                if v.judge is None and field_of(v.expectation) == self._measured
            ]
            if views:
                found = _Reading(scorer, function(scorer), views)
        self._known[digest] = found
        return found


def _pattern(data: JsonValue, measured: str) -> tuple[str | None, str | None]:
    target = data.get(measured) if isinstance(data, dict) else None
    pattern = target.get("pattern") if isinstance(target, dict) else None
    if not isinstance(pattern, str):
        return None, None
    try:
        _ = Pattern(pattern)
    except Invalid as e:
        return pattern, str(e)
    return pattern, None


def _alternatives(pattern: str | None, problem: str | None) -> list[Pattern]:
    if pattern is None or problem is not None:
        return []
    return [Pattern(a) for a in Pattern(pattern).alternatives()]


def _finding(alternatives: list[Pattern], text: _Text) -> list[int]:
    if not text.found or text.texts is None:
        return []
    marked = [text.texts[m.item] for m in text.marks]
    return [
        i
        for i, a in enumerate(alternatives)
        if any(a.spans(t) is not None for t in marked)
    ]


def _named(bench: Bench) -> Callable[[UUID], str]:
    configurations = {
        t.id: t.name or t.title for t in threads(bench, "configuration", owner=None)
    }

    def named(run: UUID) -> str:
        about = reading.about(bench.rows, Subject(run=run))
        varied = None if about.varied is None else bench.rows.edit(about.varied)
        thread = None if varied is None else varied.thread
        if thread is not None and thread in configurations:
            return configurations[thread]
        return about.name or str(run)[:8]

    return named
