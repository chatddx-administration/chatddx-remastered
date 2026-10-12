from chatddx.core.rig import entry
from chatddx.factors.scoring import Scorer

from . import metrics
from .scorer import Metrics

SCORERS: dict[str, Metrics] = {"chatddx.scorers.metrics:score": metrics.score}


def problems(scorer: Scorer) -> list[str]:
    try:
        found = entry(SCORERS, scorer.entry_point, scorer.version)
    except LookupError as e:
        return [str(e)]
    return found.problems(scorer)


def function(scorer: Scorer) -> Metrics:
    if found := problems(scorer):
        raise LookupError("; ".join(found))
    return SCORERS[scorer.entry_point]
