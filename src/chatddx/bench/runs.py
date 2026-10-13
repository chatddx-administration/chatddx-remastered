import threading
from collections.abc import Callable, Collection, Generator
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from uuid import UUID

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


@dataclass(frozen=True)
class ScorerStarted:
    scorer: str
    name: str
    score: UUID


type ScoringEvent = Event | ScorerStarted


class ScoreHalt:
    def __init__(self) -> None:
        self._guard: threading.Lock = threading.Lock()
        self._set: bool = False
        self._grading: Grading | None = None

    def set(self) -> None:
        with self._guard:
            self._set = True
            grading = self._grading
        if grading is not None:
            grading.halt()

    def is_set(self) -> bool:
        return self._set

    @contextmanager
    def watching(self, grading: Grading) -> Generator[None]:
        with self._guard:
            self._grading = grading
            halted = self._set
        if halted:
            grading.halt()
        try:
            yield
        finally:
            with self._guard:
                self._grading = None


def score(
    seen: Seen,
    run: RunStarted,
    scorers: Collection[str] | None = None,
    on_event: Callable[[ScoringEvent], None] | None = None,
    halt: ScoreHalt | None = None,
) -> list[Graded]:
    found: list[Graded] = []
    stopped = False
    for edit, about in seen.scorers_for(run):
        if scorers is not None and edit.digest not in scorers:
            continue
        name = about.name or seen.catalog.title(edit.thread)
        scorer = resolve(seen.get, edit.digest, Scorer)
        labels = seen.labels_of(edit)
        if stopped or (halt is not None and halt.is_set()):
            stopped = True
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
        if on_event is not None:
            on_event(ScorerStarted(edit.digest, name, grading.score))
        failed: str | None = None
        try:
            with nullcontext() if halt is None else halt.watching(grading):
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
