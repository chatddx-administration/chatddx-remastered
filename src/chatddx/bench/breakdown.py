import math
from collections import Counter
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, stdev
from uuid import UUID

from chatddx.factors.base import resolve
from chatddx.factors.gatherer import gather
from chatddx.factors.gathering import BASELINE, Center
from chatddx.factors.request import Skeleton

from .observed import Observed, Ran, observed
from .seen import Seen

type View = tuple[str, int]


@dataclass(frozen=True)
class Estimate:
    """A mean of `n` values with the half-width of its 95% interval, None for fewer
    than two."""

    mean: float
    half: float | None
    n: int


@dataclass(frozen=True)
class Point:
    """One baseline gathering of a configuration: `means` over its replicates alone,
    `spread` and `alike` its repeats against them."""

    started: UUID
    at: datetime
    version: int
    means: dict[View, float]
    spread: dict[View, float]
    alike: tuple[int, int]
    languages: dict[str | None, int]
    failed: float
    seconds: float
    tokens: float | None
    stale: bool


@dataclass(frozen=True)
class Pooled:
    """The baseline gatherings of the versions that compile to one skeleton, by its
    digest: each view's estimate over every replicate of every case, and its mean
    difference from the pooled before it on the cases both sent, case by case."""

    digest: str
    versions: tuple[int, ...]
    points: tuple[Point, ...]
    estimates: dict[View, Estimate]
    paired: dict[View, Estimate]


@dataclass(frozen=True)
class Peer:
    """Another configuration's latest baseline gathering, on the views it shares with
    the one broken down."""

    configuration: int
    point: Point
    shared: tuple[View, ...]


@dataclass(frozen=True)
class Breakdown:
    """How a configuration fared on the baseline cases: the views its skeleton offers,
    its versions pooled by what they compile to in the order first saved, and its
    peers among the configurations given."""

    views: tuple[View, ...]
    timeline: tuple[Pooled, ...]
    peers: tuple[Peer, ...]


def breakdown(
    seen: Seen, thread: int, cases: Collection[str], peers: Collection[int] = ()
) -> Breakdown:
    """How the configuration fared on the cases, as the baseline gatherings of its
    versions and of the peers' latest have it. A baseline is a start of runs of none
    but the cases on one seed each, as Run starts one, of no parts replaced. Costs what
    `observed` costs for each of the person's runs, cached rows costing nothing, and
    each configuration's head resolved."""
    within = set(cases)
    offered = _offered(seen)
    views = offered(_head(seen, thread))
    starts = _baselines(seen, observed(seen, seen.runs()), within)
    mine = sorted(
        (p for p in starts if p.ran[0].configuration == thread),
        key=lambda s: s.ran[0].at,
    )
    pooled: dict[str, list[_Start]] = {}
    for s in mine:
        digest = s.ran[0].digest
        assert digest is not None
        pooled.setdefault(digest, []).append(s)
    order = sorted(pooled, key=lambda d: min(s.ran[0].version or 0 for s in pooled[d]))
    timeline: list[Pooled] = []
    for digest in order:
        held = pooled[digest]
        values = _by_case(held)
        before = timeline[-1] if timeline else None
        timeline.append(
            Pooled(
                digest=digest,
                versions=tuple(sorted({s.ran[0].version or 0 for s in held})),
                points=tuple(s.point for s in held),
                estimates={
                    v: e
                    for v in views
                    if (
                        e := _estimate(
                            [x for xs in values.get(v, {}).values() for x in xs]
                        )
                    )
                },
                paired={}
                if before is None
                else _paired(views, _by_case(pooled[before.digest]), values),
            )
        )
    found: list[Peer] = []
    for other in peers:
        if other == thread:
            continue
        theirs = [s for s in starts if s.ran[0].configuration == other]
        shared = tuple(v for v in offered(_head(seen, other)) if v in views)
        if theirs and shared:
            latest = max(theirs, key=lambda s: s.ran[0].at)
            found.append(Peer(other, latest.point, shared))
    return Breakdown(views, tuple(timeline), tuple(found))


@dataclass(frozen=True)
class _Start:
    ran: tuple[Ran, ...]
    replicates: tuple[Observed, ...]
    point: Point


def _head(seen: Seen, thread: int) -> Skeleton:
    edit, _ = seen.thread(thread, "configuration")
    return resolve(seen.store.get, edit.digest, Skeleton)


def _offered(seen: Seen) -> Callable[[Skeleton], tuple[View, ...]]:
    scorers = [s for _, _, s in seen.scorers()]

    def offered(skeleton: Skeleton) -> tuple[View, ...]:
        return tuple(
            (s.digest, i)
            for s in scorers
            for i, v in enumerate(s.views)
            if v.offered_by(skeleton.output_schema)
        )

    return offered


def _baselines(seen: Seen, found: Sequence[Observed], within: set[str]) -> list[_Start]:
    starts: dict[tuple[int, UUID], list[Observed]] = {}
    for o in found:
        r = o.ran
        if r.configuration is None or r.replaced:
            continue
        starts.setdefault((r.configuration, r.started_with), []).append(o)
    made: list[_Start] = []
    for each in starts.values():
        if not all(set(o.ran.cases) <= within and len(o.ran.seeds) == 1 for o in each):
            continue
        by_run = {o.ran.run: o for o in each}
        held = gather(
            Center(component=each[0].ran.skeleton),
            BASELINE,
            [
                (o.ran.skeleton, o.ran.run, o.ran.trial)
                for o in sorted(each, key=lambda o: o.ran.at)
            ],
            seen.store.get,
        )
        if held is None:
            continue
        groups = held.groups()
        replicates = tuple(
            by_run[g["replicates"].run] for g in groups if "replicates" in g
        )
        repeats = {
            by_run[g["replicates"].run].ran.run: by_run[g["repeat"].run]
            for g in groups
            if "replicates" in g and "repeat" in g
        }
        if not replicates:
            continue
        made.append(
            _Start(
                tuple(o.ran for o in each),
                replicates,
                _point(each, replicates, repeats),
            )
        )
    return made


def _point(
    each: list[Observed],
    replicates: tuple[Observed, ...],
    repeats: dict[UUID, Observed],
) -> Point:
    first = min((o.ran for o in each), key=lambda r: r.at)
    means: dict[View, list[float]] = {}
    spread: dict[View, list[float]] = {}
    alike = [0, 0]
    languages: Counter[str | None] = Counter()
    for o in replicates:
        languages.update({o.ran.language: len(o.ran.cases)})
        mine = _values(o)
        for (_, view), value in mine.items():
            means.setdefault(view, []).append(value)
        repeat = repeats.get(o.ran.run)
        if repeat is None:
            continue
        theirs = _values(repeat)
        for at, value in mine.items():
            if at in theirs:
                spread.setdefault(at[1], []).append(abs(value - theirs[at]))
        said = {i.case: i.said for i in repeat.ran.items}
        for i in o.ran.items:
            if i.said is not None and said.get(i.case) is not None:
                alike[1] += 1
                alike[0] += i.said == said[i.case]
    items = [i for o in each for i in o.ran.items]
    tokens = [i.tokens for i in items if i.tokens is not None]
    return Point(
        started=first.started_with,
        at=first.at,
        version=first.version or 0,
        means={v: mean(xs) for v, xs in means.items()},
        spread={v: mean(xs) for v, xs in spread.items()},
        alike=(alike[0], alike[1]),
        languages=dict(languages),
        failed=sum(i.failed for i in items) / len(items) if items else 0.0,
        seconds=mean(i.seconds for i in items) if items else 0.0,
        tokens=mean(tokens) if tokens else None,
        stale=any(o.unscored for o in each),
    )


def _values(o: Observed) -> dict[tuple[str, View], float]:
    return {
        (case, (s.scorer, view)): value
        for s in o.scores
        for case, replicate, view, value in s.values
        if replicate == 0 and value is not None
    }


def _by_case(starts: Sequence[_Start]) -> dict[View, dict[str, list[float]]]:
    found: dict[View, dict[str, list[float]]] = {}
    for s in starts:
        for o in s.replicates:
            for (case, view), value in _values(o).items():
                found.setdefault(view, {}).setdefault(case, []).append(value)
    return found


def _paired(
    views: Sequence[View],
    before: dict[View, dict[str, list[float]]],
    after: dict[View, dict[str, list[float]]],
) -> dict[View, Estimate]:
    found: dict[View, Estimate] = {}
    for v in views:
        then, now = before.get(v, {}), after.get(v, {})
        diffs = [mean(now[c]) - mean(then[c]) for c in now if c in then]
        if (e := _estimate(diffs)) is not None:
            found[v] = e
    return found


def _estimate(values: Sequence[float]) -> Estimate | None:
    if not values:
        return None
    if len(values) < 2:
        return Estimate(values[0], None, 1)
    half = 1.96 * stdev(values) / math.sqrt(len(values))
    return Estimate(mean(values), half, len(values))
