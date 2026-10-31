from collections.abc import Hashable
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from chatddx.bench import Bench, NotFound
from chatddx.catalog import Subject, read
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import ExpectationSchema, Scorer, Scoring
from chatddx.factors.select import field as field_of
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted
from chatddx.scorers.shipped import unit_of
from chatddx.scripted.fared import drawn

from . import families as api_families, schemas
from .people import BenchDep
from .state import no_store, state
from .threads import threads

router = APIRouter(tags=["families"])


@dataclass(frozen=True)
class _Metric:
    scorer: Scorer
    view: int
    label: str
    field: str | None


@dataclass
class _Held:
    values: list[float] = field(default_factory=list[float])
    href: str | None = None


@router.get("/families/{family}/fared", dependencies=[Depends(no_store)])
def fared(
    request: Request, bench: BenchDep, family: int, case: str, expectation_schema: str
) -> schemas.Fared:
    """How the case fares under each of the person's configurations on each view of the
    scorers under the schema, among how every family's case fares: each the mean of its
    latest gathering's replicates under a configuration, as the person's runs have it,
    none where they ran but weren't scored, and, in a World that draws them, drawn where
    none ran. Views in characters are left
    out, as they aren't on the scale of the others.

    Costs a read of each of the person's runs and their scores, finished scores held
    once read; the drawing is local.
    """
    shown = api_families.family(bench, family)
    picked = next((c for c in shown.cases if c.case == case), None)
    if picked is None:
        raise NotFound(f"no case {case} of family {family}")
    configurations = sorted(
        threads(bench, "configuration", owner=bench.person.login),
        key=lambda t: t.name or t.title,
    )
    metrics = _metrics(bench, expectation_schema)
    cases = [
        schemas.FaredCase(case=f.case, family=f.id, title=f.name)
        for f in api_families.families(bench)
        if f.case != case
    ]
    cases.append(schemas.FaredCase(case=case, family=family, title=picked.title))
    at = {c.case: i for i, c in enumerate(cases)}
    measured = _measured(bench, {c.case for c in cases}, metrics)
    seed = state(request).synthetic
    rows: list[schemas.FaredRow] = []
    for m, metric in enumerate(metrics):
        for c, t in enumerate(configurations):
            output = resolve(bench.store.get, t.head.digest, Skeleton).output_schema
            if not all(v.offered_by(output) for v in metric.scorer.views):
                continue
            values: dict[int, tuple[float, int, bool, str | None]] = {}
            for one in cases:
                held = measured.get((one.case, t.id, metric.scorer.digest, metric.view))
                if held is not None:
                    if held.values:
                        values[at[one.case]] = (
                            mean(held.values),
                            len(held.values),
                            False,
                            held.href,
                        )
                elif seed is not None:
                    metric_name = metric.scorer.views[metric.view].metric
                    got = drawn(
                        seed,
                        one.case,
                        t.id,
                        metric.scorer.digest,
                        metric.view,
                        metric_name,
                    )
                    values[at[one.case]] = (mean(got), len(got), True, None)
            if not values:
                continue
            here = values.pop(at[case], None)
            rows.append(
                schemas.FaredRow(
                    metric=m,
                    configuration=c,
                    cases=list(values),
                    values=[v[0] for v in values.values()],
                    synthetic=[v[2] for v in values.values()],
                    shown=None
                    if here is None
                    else schemas.FaredShown(
                        value=here[0],
                        replicates=here[1],
                        synthetic=here[2],
                        href=here[3],
                    ),
                )
            )
    return schemas.Fared(
        synthetic=any(
            any(r.synthetic) or (r.shown and r.shown.synthetic) for r in rows
        ),
        configurations=[
            schemas.FaredConfiguration(id=t.id, name=t.name or t.title)
            for t in configurations
        ],
        metrics=[
            schemas.FaredMetric(
                scorer=m.scorer.digest, view=m.view, label=m.label, field=m.field
            )
            for m in metrics
        ],
        cases=cases,
        rows=rows,
    )


def _metrics(bench: Bench, schema: str) -> list[_Metric]:
    found: list[_Metric] = []
    for t in threads(bench, "scorer"):
        scorer = resolve(bench.store.get, t.head.digest, Scorer)
        if scorer.expectation_schema != schema:
            continue
        labels = bench.labels(scorer.digest)
        title = t.name or t.title
        found.extend(
            _Metric(
                scorer,
                i,
                f"{title} › {labels.get(i, str(i))}",
                field_of(v.expectation),
            )
            for i, v in enumerate(scorer.views)
            if unit_of(scorer, i) != "@"
        )
    held = resolve(bench.store.get, schema, ExpectationSchema).json_schema
    properties = held.get("properties")
    order = list(properties) if isinstance(properties, dict) else []
    return sorted(
        found,
        key=lambda m: (
            order.index(m.field) if m.field in order else len(order),
            m.label.split(" › ")[0],
            m.view,
        ),
    )


type _Key = tuple[str, int, str, int]


# Policy: a case's latest gathering under a configuration is the runs started together
# with its latest run reaching it, each read by its latest score under each scorer.
def _measured(
    bench: Bench, cases: set[str], metrics: list[_Metric]
) -> dict[_Key, _Held]:
    runs = bench.runs()
    abouts = read.abouts(bench.rows, [Subject(run=r.run) for r in runs])
    latest: dict[tuple[str, int], tuple[datetime, Hashable]] = {}
    gathered: dict[tuple[str, int, Hashable], list[RunStarted]] = {}
    for r in runs:
        about = abouts[Subject(run=r.run)]
        varied = None if about.varied is None else bench.rows.edit(about.varied)
        if varied is None:
            continue
        together = about.started_with or r.run
        for one in set(resolve(bench.store.get, r.trial, Trial).cases) & cases:
            at = (one, varied.thread)
            gathered.setdefault((*at, together), []).append(r)
            if at not in latest or latest[at][0] < r.at:
                latest[at] = (r.at, together)
    wanted = {(m.scorer.digest, m.view) for m in metrics}
    found: dict[_Key, _Held] = {}
    for (one, configuration), (_, together) in latest.items():
        for r in gathered[one, configuration, together]:
            for score, scorer in _latest_scores(bench, r.run).items():
                for item in bench.store.score(score).items:
                    if item.key.case != one or (scorer, item.view) not in wanted:
                        continue
                    held = found.setdefault(
                        (one, configuration, scorer, item.view), _Held()
                    )
                    if item.value is not None:
                        held.values.append(item.value)
                    if held.href is None:
                        held.href = (
                            f"/scores/{score}/{one}/{item.key.replicate}/{item.view}"
                        )
    return found


def _latest_scores(bench: Bench, run: UUID) -> dict[UUID, str]:
    latest: dict[str, tuple[datetime, UUID]] = {}
    for started in bench.store.scores_of(run):
        scorer = resolve(bench.store.get, started.scoring, Scoring).scorer
        if scorer not in latest or latest[scorer][0] < started.at:
            latest[scorer] = (started.at, started.score)
    return {score: scorer for scorer, (_, score) in latest.items()}
