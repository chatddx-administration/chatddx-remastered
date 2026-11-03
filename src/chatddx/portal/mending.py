from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager, suppress
from uuid import UUID

from chatddx.api import schemas
from chatddx.api.standing import Seeds, Standing
from chatddx.api.state import refused
from chatddx.bench import Bench, Endpoint, NotFound, TriedVariation
from chatddx.factors.base import Invalid
from chatddx.factors.gathering import Seeding
from chatddx.factors.trial import suggest_seeds
from chatddx.ledger import RunStarted
from chatddx.runner import Refused, Running
from chatddx.store import UnderWay


def mend(
    bench: Bench,
    stood: Sequence[Standing],
    cases: Sequence[str],
    seedings: tuple[Seeding, ...],
    left: Callable[[RunStarted], list[str]],
) -> bool:
    """Does what Run does about each configuration's gathering on the cases, in the
    seedings' shape, as it stands: runs it again on the seeds it holds, drawing the
    rest, resumes what stopped and scores again by the scorers `left` gives. Says
    whether it began any run, or had none to begin. Costs a start of the cases for each
    seeding of each configuration run again, all queued once begun, and a queueing of
    each run resumed or scored."""
    behind = [(s.configuration, b) for s in stood for b in s.behind]
    rerun = [
        (s.configuration, s.version, b.rerun)
        for s in stood
        for b in s.behind
        if b.rerun is not None
    ]
    bench.check_quota([len(cases) * s.seeds for _ in rerun for s in seedings])
    first: UUID | None = None
    begun: list[Running] = []
    with _queueing(bench, begun):
        for t, at, seeds in rerun:
            begun += _begin(bench, t, at, cases, first, seeds, seedings)
            first = first or (begun[0].started.run if begun else None)
    for _, b in behind:
        for run in b.resume:
            with pressed():
                _ = bench.queue(bench.resume(bench.run(run)))
        for run in b.rescore:
            if scorers := left(bench.run(run)):
                with pressed():
                    _ = bench.queue_scoring(bench.run(run), scorers)
    return not rerun or first is not None


def placed(
    bench: Bench, t: schemas.Thread, at: int | None = None
) -> tuple[TriedVariation, Endpoint] | None:
    """The configuration as it is now, its version `at` when given, and where it runs,
    or None when it can't run."""
    if t.outdated:
        return None
    try:
        variation = bench.variation(t.id, {}, at)
        return variation, bench.at(variation)
    except (Invalid, NotFound):
        return None


def _begin(
    bench: Bench,
    t: schemas.Thread,
    at: int | None,
    cases: Sequence[str],
    first: UUID | None,
    seeds: Seeds,
    seedings: tuple[Seeding, ...],
) -> list[Running]:
    if (at_hand := placed(bench, t, at)) is None:
        return []
    variation, endpoint = at_hand
    drawn: dict[str, tuple[int, ...]] = {}
    begun: list[Running] = []
    for s in seedings:
        each = drawn[s.name] = (
            seeds[s.name]
            if s.name in seeds
            else suggest_seeds(s.seeds)
            if s.repeats is None
            else drawn[s.repeats][-s.seeds :]
        )
        joining = first or (begun[0].started.run if begun else None)
        try:
            started = bench.start(
                variation, endpoint.name, list(cases), each, joining=joining
            )
        except (Invalid, Refused):
            break
        begun += [running for _, running in started.runs]
    return begun


# Policy: a press made while something is under way for its run, from a second tab, a
# stale page or a second click, counts as made: the page it leads back to says so.
@contextmanager
def pressed() -> Generator[None]:
    with refused(), suppress(UnderWay):
        yield


# Policy: queued once every run is begun, so that the worker sending the first doesn't
# slow beginning the rest, and queued too when beginning one fails, so that none is left
# begun with nothing to send it.
@contextmanager
def _queueing(bench: Bench, begun: list[Running]) -> Generator[None]:
    try:
        yield
    finally:
        with bench.conn.transaction():
            for running in begun:
                _ = bench.queue(running, True)
