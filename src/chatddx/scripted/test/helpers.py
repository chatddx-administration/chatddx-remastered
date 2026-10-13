from chatddx.bench import Bench, outcome
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted

UNFINISHED = "Unfinished: the stream ended before [DONE]"


def went(bench: Bench, started: RunStarted) -> dict[str, tuple[str, str | None]]:
    trial = resolve(bench.get, started.trial, Trial)
    skeleton = resolve(bench.get, trial.skeleton, Skeleton)
    return {
        bench.title(item.key.case): outcome(skeleton, item)
        for item in bench.store.run(started.run).items
    }
