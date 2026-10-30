from pydantic import JsonValue

from chatddx.factors.scoring import Scorer
from chatddx.rig import entry

from . import metrics
from .scorer import Metrics, reading, refusals

SCORERS: dict[str, Metrics] = {"chatddx.scorers.metrics:score": metrics.score}


def problems(scorer: Scorer) -> list[str]:
    try:
        found = entry(SCORERS, scorer.entry_point, scorer.version)
    except LookupError as e:
        return [str(e)]
    return found.problems(scorer)


def unit_of(scorer: Scorer, view: int) -> str:
    code = SCORERS.get(scorer.entry_point)
    metric = None if code is None else code.metrics.get(scorer.views[view].metric)
    return (metric.unit or "") if metric is not None else ""


def function(scorer: Scorer) -> Metrics:
    if found := problems(scorer):
        raise LookupError("; ".join(found))
    return SCORERS[scorer.entry_point]


def read_by(scorer: Scorer, data: JsonValue) -> list[object]:
    return reading(scorer, function(scorer), data)


def refused(scorer: Scorer, data: JsonValue) -> list[tuple[str, Exception]]:
    code = SCORERS.get(scorer.entry_point)
    return [] if code is None else refusals(scorer, code, data)
