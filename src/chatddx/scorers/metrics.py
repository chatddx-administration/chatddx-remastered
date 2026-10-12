from . import patterns, verdicts
from .scorer import Metrics

score = Metrics(2, {**patterns.METRICS, **verdicts.METRICS})
