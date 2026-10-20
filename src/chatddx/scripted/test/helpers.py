from chatddx.bench import Bench
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted
from chatddx.runner import outcome
from chatddx.scripted import RUNS, ran_before, scripted_runs
from chatddx.test.world import TEST

UNFINISHED = "Unfinished: the stream ended before [DONE]"
HELD = {s.name: s for s in scripted_runs(TEST / RUNS)}


def went(bench: Bench, started: RunStarted) -> dict[str, tuple[str, str | None]]:
    trial = resolve(bench.store.get, started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    return {
        bench.title(item.key.case): outcome(skeleton, item)
        for item in bench.store.run(started.run).items
    }


# The ran template ran each scripted run.
def held(bench: Bench, name: str) -> RunStarted:
    started = ran_before(bench, HELD[name])
    assert started is not None
    return started
