from dataclasses import dataclass
from datetime import datetime
from statistics import mean
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from chatddx.bench import Bench, NotFound
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import ExpectationSchema, Scorer, Scoring
from chatddx.factors.select import field as field_of
from chatddx.scorers.shipped import unit_of
from chatddx.scripted.fared import drawn

from . import families as api_families, schemas
from .people import BenchDep
from .standing import standing
from .state import no_store, state
from .threads import threads

router = APIRouter(tags=["families"])


@dataclass(frozen=True)
class _Metric:
    scorer: Scorer
    view: int
    label: str
    field: str | None


@router.get("/families/{family}/fared", dependencies=[Depends(no_store)])
def fared(
    request: Request, bench: BenchDep, family: int, case: str, expectation_schema: str
) -> schemas.Fared:
    """How the case fares under each of the person's configurations on each view of the
    scorers under the schema, among how every family's case fares: each the mean of its
    latest gathering's replicates under a configuration, as `bench.gatherings` has it,
    none where they ran but weren't scored, and, in a World that draws them, drawn where
    none ran; and, under each configuration, what keeps the case's latest gathering from
    being a whole 3+1 as things are now. Views in characters are left out, as they
    aren't on the scale of the others.

    Costs a read of each of the person's runs and their scores, finished scores held
    once read, and what `standing` costs; the drawing is local.
    """
    shown = api_families.family(bench, family)
    picked = next((c for c in shown.cases if c.case == case), None)
    if picked is None:
        raise NotFound(f"no case {case} of family {family}")
    expected = next(
        (e for e in picked.expectations if e.expectation_schema == expectation_schema),
        None,
    )
    marked = expected is not None and expected.expectation is not None
    stood = standing(bench, case, expectation_schema, marked)
    configurations = [s.configuration for s in stood]
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
            values: dict[int, tuple[float, bool, list[schemas.FaredReplicate]]] = {}
            for one in cases:
                held = measured.get((one.case, t.id, metric.scorer.digest, metric.view))
                if held is not None:
                    if got := [r.value for r in held if r.value is not None]:
                        values[at[one.case]] = (mean(got), False, held)
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
                    replicates = [
                        schemas.FaredReplicate(value=v, href=None) for v in got
                    ]
                    values[at[one.case]] = (mean(got), True, replicates)
            if not values:
                continue
            here = values.pop(at[case], None)
            rows.append(
                schemas.FaredRow(
                    metric=m,
                    configuration=c,
                    cases=list(values),
                    values=[v[0] for v in values.values()],
                    synthetic=[v[1] for v in values.values()],
                    shown=None
                    if here is None
                    else schemas.FaredShown(
                        value=here[0], synthetic=here[1], replicates=here[2]
                    ),
                )
            )
    behind = [b for s in stood for b in s.behind]
    return schemas.Fared(
        synthetic=any(
            any(r.synthetic) or (r.shown and r.shown.synthetic) for r in rows
        ),
        run=not any(b.why == "under_way" for b in behind)
        and any(b.rerun is not None or b.resume or b.rescore for b in behind),
        configurations=[
            schemas.FaredConfiguration(
                id=s.configuration.id,
                name=s.configuration.name or s.configuration.title,
                behind=[
                    schemas.FaredBehind(
                        why=b.why,
                        refusal=None
                        if b.refusal is None
                        else schemas.Error.of(b.refusal, "refused"),
                        language=b.language,
                    )
                    for b in s.behind
                ],
            )
            for s in stood
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


def _measured(
    bench: Bench, cases: set[str], metrics: list[_Metric]
) -> dict[_Key, list[schemas.FaredReplicate]]:
    wanted = {(m.scorer.digest, m.view) for m in metrics}
    found: dict[_Key, list[schemas.FaredReplicate]] = {}
    for (one, configuration), runs in bench.gatherings(cases).items():
        for r in reversed(runs):
            for score, scorer in _latest_scores(bench, r.run).items():
                for item in bench.store.score(score).items:
                    if item.key.case != one or (scorer, item.view) not in wanted:
                        continue
                    href = f"/scores/{score}/{one}/{item.key.replicate}/{item.view}"
                    found.setdefault(
                        (one, configuration, scorer, item.view), []
                    ).append(schemas.FaredReplicate(value=item.value, href=href))
    return found


def _latest_scores(bench: Bench, run: UUID) -> dict[UUID, str]:
    latest: dict[str, tuple[datetime, UUID]] = {}
    for started in bench.store.scores_of(run):
        scorer = resolve(bench.store.get, started.scoring, Scoring).scorer
        if scorer not in latest or latest[scorer][0] < started.at:
            latest[scorer] = (started.at, started.score)
    return {score: scorer for scorer, (_, score) in latest.items()}
