from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import NamedTuple, Protocol

from jsonschema import validators
from jsonschema.exceptions import relevance
from pydantic import JsonValue

from chatddx.factors.scoring import Scorer


class Scored(NamedTuple):
    value: float | None
    detail: JsonValue = None


# A judged view's verdicts, one per seed of its judge, each none when it couldn't be read.
type Verdicts = list[JsonValue | None]


class ScoreFunction(Protocol):
    def __call__(
        self,
        metric: str,
        output: list[JsonValue] | None,
        expected: list[JsonValue],
        params: Mapping[str, JsonValue],
        verdicts: Verdicts | None = None,
    ) -> Scored: ...


MetricFunction = Callable[
    [list[JsonValue] | None, list[JsonValue], Mapping[str, JsonValue], Verdicts | None],
    Scored,
]

NO_PARAMS: dict[str, JsonValue] = {"type": "object", "additionalProperties": False}


def _no_params() -> dict[str, JsonValue]:
    return dict(NO_PARAMS)


@dataclass(frozen=True)
class Metric:
    measures: str
    score: MetricFunction
    params: dict[str, JsonValue] = field(default_factory=_no_params)
    judged: bool = False


class Metrics:
    def __init__(
        self,
        version: int,
        metrics: Mapping[str, Metric],
        params: dict[str, JsonValue] | None = None,
    ) -> None:
        self.version: int = version
        self.metrics: dict[str, Metric] = dict(metrics)
        self.params: dict[str, JsonValue] | None = params

    @property
    def names(self) -> frozenset[str]:
        return frozenset(self.metrics)

    def __call__(
        self,
        metric: str,
        output: list[JsonValue] | None,
        expected: list[JsonValue],
        params: Mapping[str, JsonValue],
        verdicts: Verdicts | None = None,
    ) -> Scored:
        found = self.metrics.get(metric)
        if found is None:
            raise ValueError(f"no metric {metric!r}, only {sorted(self.metrics)}")
        return found.score(output, expected, params, verdicts)

    def problems(self, scorer: Scorer) -> list[str]:
        found: list[str] = []
        if unknown := sorted({v.metric for v in scorer.views} - self.names):
            found.append(
                f"{scorer.entry_point} knows no metric {', '.join(unknown)}, "
                + f"only {', '.join(sorted(self.names))}"
            )
        shared = self.params if self.params is not None else NO_PARAMS
        if (refused := _refused(shared, scorer.params)) is not None:
            found.append(f"the scorer's params {refused}")
        for i, view in enumerate(scorer.views):
            metric = self.metrics.get(view.metric)
            if metric is None:
                continue
            if metric.judged and view.judge is None:
                found.append(
                    f"view {i}'s metric {view.metric} reads a judge's verdicts"
                )
            if view.judge is not None and not metric.judged:
                found.append(
                    f"view {i} names a judge, which {view.metric} doesn't read"
                )
            if (refused := _refused(metric.params, view.params)) is not None:
                found.append(f"view {i}'s params for {view.metric} {refused}")
        return found


def _refused(
    schema: dict[str, JsonValue], params: Mapping[str, JsonValue]
) -> str | None:
    check = validators.validator_for(schema)(schema)
    error = max(check.iter_errors(dict(params)), key=relevance, default=None)
    if error is None:
        return None
    where = "/".join(str(p) for p in error.absolute_path)
    return f"at /{where}: {error.message}" if where else f"don't fit: {error.message}"


def score(
    scorer: Scorer,
    run: ScoreFunction,
    answer: JsonValue | None,
    data: JsonValue,
    verdicts: Mapping[int, Verdicts] | None = None,
) -> list[Scored]:
    judged = verdicts or {}
    if unjudged := [
        i for i, v in enumerate(scorer.views) if v.judge is not None and i not in judged
    ]:
        raise NotImplementedError(f"views {unjudged} need a judge, which can't run yet")
    return [
        score_view(scorer, run, i, answer, data, judged.get(i))
        for i in range(len(scorer.views))
    ]


def score_view(
    scorer: Scorer,
    run: ScoreFunction,
    index: int,
    answer: JsonValue | None,
    data: JsonValue,
    verdicts: Verdicts | None = None,
) -> Scored:
    view = scorer.views[index]
    return run(
        view.metric,
        None if answer is None else view.output_items(answer),
        view.expectation_items(data),
        scorer.params | view.params,
        verdicts,
    )
