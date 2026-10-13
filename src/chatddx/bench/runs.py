from collections.abc import Callable, Collection

from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.ledger import RunStarted
from chatddx.runner.gate import Refused
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import Event, Grader, Grading
from chatddx.runner.send import STOPPED

from .configurations import keep_compilation
from .model import Graded
from .seen import Seen
from .variation import TriedVariation

REFUSALS = (LookupError, TypeError, ValueError, NotImplementedError, Refused)


def start(
    seen: Seen, variation: TriedVariation, endpoint: str, cases: list[str], seed: int
) -> Running:
    skeleton = seen.skeleton(variation)
    if skeleton.purpose == "judge":
        raise ValueError(
            f"{variation.label} is a judge configuration: a judge is asked as runs are "
            + "scored, and isn't run on cases"
        )
    registry, trial = seen.trial(skeleton, seen.endpoint(endpoint), cases, seed)
    runner = Runner(seen.conn, seen.inventory, seen.person)
    running = runner.start(trial, registry, endpoint)
    _ = keep_compilation(seen, variation)
    return running


def score(
    seen: Seen,
    run: RunStarted,
    scorers: Collection[str] | None = None,
    on_event: Callable[[Event], None] | None = None,
) -> list[Graded]:
    found: list[Graded] = []
    stopped = False
    for edit, about in seen.scorers_for(run):
        if scorers is not None and edit.digest not in scorers:
            continue
        name = about.name or seen.catalog.title(edit.thread)
        scorer = resolve(seen.get, edit.digest, Scorer)
        labels = seen.labels_of(edit)
        if stopped:
            found.append(Graded(name, scorer, labels, refused=STOPPED))
            continue
        try:
            grading = _started(seen, run, edit.digest)
        except REFUSALS as e:
            found.append(Graded(name, scorer, labels, refused=str(e)))
            continue
        except KeyboardInterrupt:
            stopped = True
            found.append(Graded(name, scorer, labels, refused=STOPPED))
            continue
        failed: str | None = None
        try:
            grading.send(on_event)
        except KeyboardInterrupt:
            stopped = True
        except REFUSALS as e:
            failed = str(e)
        given, findings = grading.finish()
        if failed is None:
            found.append(Graded(name, scorer, labels, given, findings))
        else:
            found.append(Graded(name, scorer, labels, refused=failed))
    return sorted(found, key=lambda g: g.name)


def _started(seen: Seen, run: RunStarted, scorer: str) -> Grading:
    scoring = seen.scoring(run, scorer)
    if scoring is None:
        raise LookupError("none of the run's cases has an expectation")
    registry = seen.store.load([scoring.scorer, *scoring.expectations])
    grader = Grader(seen.conn, seen.inventory, seen.person)
    return grader.start(run.run, scoring, registry)
