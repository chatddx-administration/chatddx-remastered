from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import get_args
from uuid import UUID

from chatddx import settings
from chatddx.catalog import Entry, EntryField, Subject, read, titles
from chatddx.catalog.families import family_of
from chatddx.factors.base import resolve
from chatddx.factors.cases import Case, CleanupOp
from chatddx.factors.engine import model_of
from chatddx.factors.request import RECIPE_PARTS, Skeleton
from chatddx.factors.trial import CanarySet, Execution, Trial
from chatddx.ledger import RunStarted
from chatddx.ledger.run import PHASES, Phase
from chatddx.runner import STOPPED, Grading, Halt, Refused, Runner, Running, ScoreEvent
from chatddx.store import Job, Queue

from .configurations import keep_compilation
from .errors import NotFound, OverQuota
from .model import Carried, Graded, Started
from .seen import Seen, labels_of, scoring, trial
from .variation import TriedVariation

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
    seen_cases = {c for f in seen.families() for c in f.cases}
    if missing := [c for c in cases if c not in seen_cases]:
        raise NotFound(f"no case {missing[0]} for {seen.person.login}")
    carried = seen.languages(variation, cases)
    sent = [c for c in carried if c.skeleton is not None]
    left_out = [c for c in carried if c.skeleton is None]
    if not sent:
        raise ValueError(
            "no case can be sent: " + "; ".join(c.refused or "" for c in left_out)
        )
    at = seen.at(variation, endpoint)
    canaries = canaries or at.spec.canaries
    _check_quota(seen, [len(c.cases) * len(seeds) for c in sent])
    said = _varying(
        variation.configuration.id,
        {p: variation.parts[p][0] for p in RECIPE_PARTS if p in variation.parts},
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
                at.name,
                at.engine,
                each.cases,
                seeds,
                variation.label,
                [*said, *with_first],
                cleanup=_cleanup_of(seen, each.cases)
                if cleanup is None
                else tuple(cleanup),
                execution=execution or at.spec.execution,
                canaries=None
                if canaries is None
                else resolve(seen.store.get, canaries, CanarySet),
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
    ran = resolve(seen.store.get, run.trial, Trial)
    families = {f.id for f in seen.families()}
    if missing := [c for c in ran.cases if family_of(seen.rows, c) not in families]:
        raise NotFound(f"no case {missing[0]} for {seen.person.login}")
    skeleton = resolve(seen.store.get, ran.skeleton, Skeleton)
    about = read.about(seen.rows, Subject(run=run.run))
    weights = model_of(ran.engine, seen.store.get).digest
    handle = seen.handle(weights)
    if handle.weights != weights:
        raise ValueError(
            f"run {run.run} ran weights {handle.name} no longer holds: run its "
            + "configuration, followed, instead"
        )
    at = seen.served(handle)
    return _begun(
        seen,
        skeleton,
        at.name,
        at.engine,
        list(ran.cases),
        seeds,
        about.name or seen.title(ran.skeleton),
        _varying(about.varied, about.replaced),
        cleanup=ran.cleanup,
        execution=run.execution,
        canaries=None
        if run.canaries is None
        else resolve(seen.store.get, run.canaries, CanarySet),
        verify_at=run.verify_at,
    )


def _varying(edit: int | None, replaced: Mapping[str, str | None]) -> list[Entry]:
    if edit is None:
        return []
    return [Entry.varied(edit), *(Entry.replaced(p, d) for p, d in replaced.items())]


def resume(seen: Seen, run: RunStarted) -> Running:
    return Runner(seen.conn, seen.inventory, seen.person).resume(run.run)


def queue(seen: Seen, running: Running, score: bool = True) -> Job:
    started = running.started
    assert started.endpoint is not None
    return Queue(seen.conn).put(
        seen.person.id,
        started.run,
        started.endpoint.name,
        started.execution.concurrency,
        score,
    )


def queue_scoring(
    seen: Seen, run: RunStarted, scorers: Collection[str] | None = None
) -> list[str]:
    if run.run not in seen.store.finished([run.run]):
        raise ValueError(f"run {run.run} hasn't finished")
    applying = [e.digest for e, _, _ in seen.scorers(run)]
    if missing := [s for s in scorers or () if s not in applying]:
        raise ValueError(f"scorer {missing[0]} doesn't apply to run {run.run}")
    chosen = [s for s in applying if scorers is None or s in scorers]
    if not chosen:
        raise ValueError(f"no scorer applies to run {run.run}")
    endpoint = "" if run.endpoint is None else run.endpoint.name
    _ = Queue(seen.conn).put(seen.person.id, run.run, endpoint, 0, True, chosen)
    return chosen


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
    registry, made = trial(seen, skeleton, engine, cases, seeds, cleanup)
    runner = Runner(seen.conn, seen.inventory, seen.person)
    running = runner.start(made, registry, endpoint, execution, canaries, verify_at)
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
    started = seen.rows.runs_started(seen.person.id, since)
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


type ScoringEvent = ScoreEvent | ScorerStarted


def score(
    seen: Seen,
    run: RunStarted,
    scorers: Collection[str] | None = None,
    on_event: Callable[[ScoringEvent], None] | None = None,
    halt: Halt | None = None,
) -> list[Graded]:
    found: list[Graded] = []
    stopped = False
    for edit, about, scorer in seen.scorers(run):
        if scorers is not None and edit.digest not in scorers:
            continue
        name = about.name or titles.title(seen.rows, edit.thread)
        labels = labels_of(seen, edit)
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
            grading.send(on_event, halt)
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
    built = scoring(seen, run, scorer)
    if built is None:
        raise LookupError("none of the run's cases has an expectation")
    registry = seen.store.load([built.scorer, *built.expectations])
    runner = Runner(seen.conn, seen.inventory, seen.person)
    return runner.score(run.run, built, registry)
