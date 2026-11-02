from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

from chatddx.bench import Bench, NotFound
from chatddx.bench.seen import trial
from chatddx.factors.base import Invalid, resolve
from chatddx.factors.gatherer import gather
from chatddx.factors.gathering import REPLICATED, Center
from chatddx.factors.scoring import Scorer
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted
from chatddx.runner import Refused
from chatddx.runner.gate import bar
from chatddx.store import Queue

from . import schemas
from .threads import threads

OPEN = ("queued", "under way")

type Why = Literal[
    "under_way",
    "outdated",
    "untranslated",
    "refused",
    "no_runs",
    "not_whole",
    "changed",
    "halted",
    "unfinished",
    "unscored",
]

type Seeds = Mapping[str, tuple[int, ...]]


@dataclass(frozen=True)
class Behind:
    """Why a case's latest gathering under a configuration isn't a whole 3+1 as things
    are now, and what Run does about it: runs it again on `rerun`'s seeds, drawing
    those it doesn't hold, resumes `resume` and scores `rescore` again."""

    why: Why
    refusal: Exception | None = None
    language: str | None = None
    rerun: Seeds | None = None
    resume: tuple[UUID, ...] = ()
    rescore: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class Standing:
    configuration: schemas.Thread
    runs: list[RunStarted]
    behind: list[Behind] = field(default_factory=list[Behind])


def configurations(bench: Bench) -> list[schemas.Thread]:
    """The person's own configurations that generate, by name."""
    found = threads(bench, "configuration", owner=bench.person.login)
    return sorted(found, key=lambda t: t.name or t.title)


def standing(
    bench: Bench, case: str, schema: str | None, marked: bool
) -> list[Standing]:
    """How the case's latest gathering stands under each of the person's
    configurations, as `bench.gatherings` has it: under way, or what keeps it from
    being a whole 3+1 of the configuration as it is now, scored under the schema
    against the expectation, if `marked`, as it is now. Costs the person's runs read,
    their places in the queue, and, for each configuration, its trial built twice and
    gated and its runs' scorings built."""
    latest = bench.gatherings([case])
    ids = [r.run for runs in latest.values() for r in runs]
    placed = Queue(bench.conn).placed(ids)
    finished = bench.store.finished(ids)

    def status(run: UUID) -> str | None:
        held = placed.get(run)
        return None if held is None else held.job.status

    found: list[Standing] = []
    for t in configurations(bench):
        runs = latest.get((case, t.id), [])
        behind = _behind(bench, t, case, runs, status, finished, schema, marked)
        found.append(Standing(t, runs, behind))
    return found


def _behind(
    bench: Bench,
    t: schemas.Thread,
    case: str,
    runs: list[RunStarted],
    status: Callable[[UUID], str | None],
    finished: set[UUID],
    schema: str | None,
    marked: bool,
) -> list[Behind]:
    if any(status(r.run) in OPEN for r in runs):
        return [Behind("under_way")]
    if (refused := _unrunnable(bench, t, case)) is not None:
        return [refused]
    if not runs:
        return [Behind("no_runs", rerun={})]
    held = gather(
        Center(component=case),
        REPLICATED,
        [(t.id, r.run, r.trial) for r in runs],
        bench.store.get,
    )
    group = {} if held is None else held.groups()[0]
    seeds = {
        s: resolve(bench.store.get, g.trial, Trial).seeds for s, g in group.items()
    }
    if len(group) < len(REPLICATED) or len(runs) > len(group):
        return [Behind("not_whole", rerun=seeds)]
    head = group[REPLICATED[0].name]
    if _trial_now(bench, t, case, seeds[head.seeding]) != head.trial:
        return [Behind("changed", rerun=seeds)]
    if any(status(g.run) == "stopped" for g in group.values()):
        return [Behind("halted", rerun=seeds)]
    found: list[Behind] = []
    if unsent := tuple(g.run for g in group.values() if g.run not in finished):
        found.append(Behind("unfinished", resume=unsent))
    by_run = {r.run: r for r in runs}
    if marked and (
        unscored := tuple(
            g.run
            for g in group.values()
            if g.run in finished and stale(bench, by_run[g.run], schema)
        )
    ):
        found.append(Behind("unscored", rescore=unscored))
    return found


def _unrunnable(bench: Bench, t: schemas.Thread, case: str) -> Behind | None:
    if t.outdated:
        return Behind("outdated")
    try:
        variation = bench.variation(t.id, {}, None)
        at = bench.at(variation)
    except (Invalid, NotFound) as e:
        return Behind("refused", refusal=e)
    for each in bench.languages(variation, [case]):
        if each.skeleton is None:
            if each.untranslated:
                return Behind("untranslated", language=str(each.language))
            return Behind("refused", refusal=Invalid(each.refused or ""))
        registry, made = trial(bench, each.skeleton, at.engine, each.cases, (0,))
        try:
            bar(bench.inventory, registry.get, at.name, made)
        except Refused as e:
            return Behind("refused", refusal=e)
    return None


def _trial_now(
    bench: Bench, t: schemas.Thread, case: str, seeds: tuple[int, ...]
) -> str | None:
    variation = bench.variation(t.id, {}, None)
    at = bench.at(variation)
    for each in bench.languages(variation, [case]):
        if each.skeleton is not None:
            cleanup = bench.cleanup(each.cases)
            _, made = trial(bench, each.skeleton, at.engine, each.cases, seeds, cleanup)
            return made.digest
    return None


def stale(bench: Bench, run: RunStarted, schema: str | None) -> list[str]:
    """The scorers under the schema that the run, finished, isn't scored by as things
    are now, by digest. Costs what `bench.unscored` costs."""
    return [
        s
        for s in bench.unscored(run)
        if resolve(bench.store.get, s, Scorer).expectation_schema == schema
    ]
