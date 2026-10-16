import threading
from collections.abc import Callable, Collection, Generator, Mapping, Sequence
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import get_args
from uuid import UUID

from chatddx import settings
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.factors.base import resolve
from chatddx.factors.cases import Case, CleanupOp
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Scorer
from chatddx.factors.trial import CanarySet, Execution, Trial
from chatddx.ledger import RunStarted
from chatddx.ledger.run import PHASES, Phase
from chatddx.runner.gate import Refused
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import Event, Grader, Grading
from chatddx.runner.send import STOPPED

from .configurations import keep_compilation
from .errors import OverQuota
from .model import Carried, Graded, Started
from .seen import Seen
from .variation import PARTS, TriedVariation

REFUSALS = (LookupError, TypeError, ValueError, NotImplementedError, Refused)


def start(
    seen: Seen,
    variation: TriedVariation,
    endpoint: str | None,
    cases: list[str],
    seeds: Sequence[int],
    cleanup: Sequence[CleanupOp] | None = None,
    execution: Execution | None = None,
    canaries: str | None = None,
) -> Started:
    if seen.skeleton(variation).purpose == "judge":
        raise ValueError(
            f"{variation.label} is a judge configuration: a judge is asked as runs are "
            + "scored, and isn't run on cases"
        )
    carried = seen.languages(variation, cases)
    sent = [c for c in carried if c.skeleton is not None]
    left_out = [c for c in carried if c.skeleton is None]
    if not sent:
        raise ValueError(
            "no case can be sent: " + "; ".join(c.refused or "" for c in left_out)
        )
    endpoint, engine = seen.at(variation, endpoint)
    spec = seen.inventory.endpoint(endpoint)
    canaries = canaries or spec.canaries
    _check_quota(seen, [len(c.cases) * len(seeds) for c in sent])
    said = _varying(
        variation.configuration.id,
        {p: variation.parts[p][0] for p in PARTS if p in variation.parts},
    )
    runs: list[tuple[Carried, Running]] = []
    # One transaction, so that a run the gate refuses leaves none of the start's begun.
    with seen.conn.transaction():
        for each in sent:
            assert each.skeleton is not None
            with_first = [Entry.started_with(runs[0][1].run)] if runs else []
            running = _begun(
                seen,
                each.skeleton,
                endpoint,
                engine,
                each.cases,
                seeds,
                variation.label,
                [*said, *with_first],
                cleanup=_cleanup_of(seen, each.cases)
                if cleanup is None
                else tuple(cleanup),
                execution=execution or spec.execution,
                canaries=None
                if canaries is None
                else resolve(seen.get, canaries, CanarySet),
            )
            runs.append((each, running))
            if each.translated:
                _ = keep_compilation(seen, variation, each.language)
        _ = keep_compilation(seen, variation)
    return Started(runs, left_out)


def _cleanup_of(seen: Seen, cases: Sequence[str]) -> tuple[CleanupOp, ...]:
    if not any(s.cleanup for s in seen.inventory.sources.values()):
        return ()
    registry = seen.store.load(cases)
    asked = {
        op
        for case in cases
        for op in seen.inventory.source(
            resolve(registry.get, case, Case).vignette.source
        ).cleanup
    }
    return tuple(op for op in get_args(CleanupOp) if op in asked)


def again(seen: Seen, run: RunStarted, seeds: Sequence[int]) -> Running:
    if run.endpoint is None:
        raise ValueError(
            f"run {run.run} was sent to no endpoint, so it can't run again"
        )
    trial = resolve(seen.get, run.trial, Trial)
    skeleton = resolve(seen.get, trial.skeleton, Skeleton)
    about = seen.catalog.about(Subject(run=run.run))
    return _begun(
        seen,
        skeleton,
        run.endpoint.name,
        trial.engine,
        list(trial.cases),
        seeds,
        about.name or seen.title(trial.skeleton),
        _varying(about.varied, about.replaced),
        cleanup=trial.cleanup,
        execution=run.execution,
        canaries=None
        if run.canaries is None
        else resolve(seen.get, run.canaries, CanarySet),
        verify_at=run.verify_at,
    )


def _varying(edit: int | None, replaced: Mapping[str, str | None]) -> list[Entry]:
    if edit is None:
        return []
    return [Entry.varied(edit), *(Entry.replaced(p, d) for p, d in replaced.items())]


def resume(seen: Seen, run: UUID) -> Running:
    _ = seen.run_by_id(run)
    return Runner(seen.conn, seen.inventory, seen.person).resume(run)


def _begun(
    seen: Seen,
    skeleton: Skeleton,
    endpoint: str,
    engine: str,
    cases: list[str],
    seeds: Sequence[int],
    name: str,
    said: Sequence[Entry],
    *,
    cleanup: tuple[CleanupOp, ...],
    execution: Execution | None,
    canaries: CanarySet | None,
    verify_at: tuple[Phase, ...] = PHASES,
) -> Running:
    _check_quota(seen, [len(cases) * len(seeds)])
    registry, trial = seen.trial(skeleton, engine, cases, seeds, cleanup)
    runner = Runner(seen.conn, seen.inventory, seen.person)
    running = runner.start(trial, registry, endpoint, execution, canaries, verify_at)
    with seen.conn.transaction():
        for entry in (Entry(field=EntryField.NAME, value=name), *said):
            seen.catalog.note(Subject(run=running.run), entry, seen.person.id)
    return running


def _check_quota(seen: Seen, runs: Sequence[int]) -> None:
    for items in runs:
        if items > settings.ITEMS_PER_RUN:
            raise OverQuota(
                f"a run holds at most {settings.ITEMS_PER_RUN} items, not {items}"
            )
    since = datetime.now(UTC) - timedelta(days=1)
    started = seen.catalog.runs_started(seen.person.id, since)
    if started + len(runs) > settings.RUNS_PER_DAY:
        said = f"{seen.person.login} has started {started} runs in the last day"
        if len(runs) == 1:
            raise OverQuota(f"{said}, as many as a day takes")
        raise OverQuota(
            f"{said}, and a day takes {settings.RUNS_PER_DAY}, not {len(runs)} more"
        )


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
