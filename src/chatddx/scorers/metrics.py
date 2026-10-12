from . import patterns, verdicts
from .scorer import Metrics

score = Metrics(1, {**patterns.METRICS, **verdicts.METRICS})
