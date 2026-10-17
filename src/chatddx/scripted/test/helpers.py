from chatddx.bench import Bench
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted
from chatddx.runner.outcome import outcome

UNFINISHED = "Unfinished: the stream ended before [DONE]"


def went(bench: Bench, started: RunStarted) -> dict[str, tuple[str, str | None]]:
    trial = resolve(bench.store.get, started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    return {
        bench.title(item.key.case): outcome(skeleton, item)
        for item in bench.store.run(started.run).items
    }
