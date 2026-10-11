from chatddx.core.rig import entry
from chatddx.factors.scoring import Scorer

from . import patterns
from .scorer import Metrics

# The scoring code chatddx ships, by the entry point a scorer pins.
SCORERS: dict[str, Metrics] = {"chatddx.scorers.patterns:score": patterns.score}


# Why `scorer` can't be scored by the running code: what it pins isn't shipped, or
# the code could never score with its views.
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
