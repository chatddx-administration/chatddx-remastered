import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from unittest import mock
from uuid import UUID

from pydantic import JsonValue

from chatddx import settings
from chatddx.api.standing import baseline_cases
from chatddx.bench import Bench, TriedVariation
from chatddx.bench.seen import picked
from chatddx.factors.base import Invalid, resolve
from chatddx.factors.gathering import BASELINE, REVIEW, Seeding
from chatddx.factors.request import Sampling
from chatddx.factors.scoring import Expectation
from chatddx.factors.trial import Execution, Trial, suggest_seeds
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.runner import Refused

from .answering import Placed, Quality, clock, placing, send, turn
from .fakes import standing_in

type Sort = Literal["baseline", "review", "try"]

# Policy: a try is a configuration run once on a handful of cases, as a variation is
# tried before it is kept: no shape of a gathering's, so it stands for none.
_TRY = (Seeding(name="tried", seeds=1),)
_SHAPES: dict[Sort, tuple[Seeding, ...]] = {
    "baseline": BASELINE,
    "review": REVIEW,
    "try": _TRY,
}
# Accommodating for the fake's script, which answers requests in the order they come:
# one at a time, case by case, so that each case is answered as drawn for it.
_ONE_BY_ONE = Execution()


@dataclass(frozen=True)
class Composed:
    gatherings: dict[str, dict[Sort, int]]
    versions: dict[str, int]
    broken: int
    unfinished: int
    skipped: dict[str, str]


def composed(
    bench: Bench,
    schema: str,
    *,
    gatherings: int = 36,
    versions: int = 6,
    seed: int = 1,
    days: int = 42,
) -> Composed:
    """Writes a few weeks of composing for each of the person's configurations that
    runs: `versions` versions of it, each its sampling with a temperature drawn, and
    `gatherings` gatherings of it spread over the last `days` days, as Run starts
    them: a baseline on the World's baseline cases as each version is saved, reviews of
    a case, and tries on a handful of cases. Each version is drawn a mean quality its
    answers are drawn around, against each case's expectation under the schema, and a
    few gatherings are broken by a server that hangs up, or left with a run
    unfinished. A configuration without a recipe is gathered at its head alone.

    Sends and scores every run in the calling thread, serving each one's fakes the
    while, on ports of this machine's for endpoints the fake vLLM doesn't run; lifts
    the person's quota of runs for as long.

    Heads-up: `LookupError` when no configuration of the person's runs, or the person
    sees no case."""
    rng = random.Random(seed)
    standing, fakes, refused = standing_in(bench.inventory, bench.store.get)
    bench = Bench(bench.conn, bench.person, standing)
    placed, skipped = placing(bench, fakes, refused)
    if not placed:
        said = "; ".join(f"{n}: {why}" for n, why in skipped.items()) or "it has none"
        raise LookupError(f"no configuration of {bench.person.login}'s runs: {said}")
    cases = [f.case for f in bench.families()]
    if not cases:
        raise LookupError(f"{bench.person.login} sees no case to run")
    expected = _expected(bench, cases, schema)
    baseline = baseline_cases(bench)
    start = datetime.now(UTC) - timedelta(days=days)
    step = timedelta(days=days) / gatherings
    made: dict[str, dict[Sort, int]] = {}
    written: dict[str, int] = {}
    broken = unfinished = 0
    with mock.patch.object(settings, "RUNS_PER_DAY", 1 << 30):
        for p in placed:
            name = p.variation.label
            heads = _versions(bench, rng, p.variation, versions)
            written[name] = len(heads)
            counted: dict[Sort, int] = {}
            seen: set[int] = set()
            for n, at in enumerate(_order(rng, len(heads), gatherings)):
                head, mean = heads[at]
                sort = _sort(rng, at in seen, bool(baseline))
                seen.add(at)
                picked_cases = (
                    baseline
                    if sort == "baseline"
                    else [rng.choice(cases)]
                    if sort == "review"
                    else sorted(rng.sample(cases, min(len(cases), rng.randint(3, 6))))
                )
                fault = rng.random()
                breaking, leaving = fault < 0.06, 0.06 <= fault < 0.1
                when = start + step * n + timedelta(minutes=rng.randrange(0, 600))
                with clock(when):
                    ran = _gather(
                        bench,
                        bench.variation(head.thread, {}, head.id),
                        p,
                        fakes,
                        picked_cases,
                        _SHAPES[sort],
                        rng,
                        {c: Quality(expected.get(c, {}), mean) for c in picked_cases},
                        breaking,
                        leaving,
                    )
                if ran:
                    counted[sort] = counted.get(sort, 0) + 1
                    broken += breaking
                    unfinished += leaving
            made[name] = counted
    return Composed(made, written, broken, unfinished, skipped)


def _expected(
    bench: Bench, cases: list[str], schema: str
) -> dict[str, dict[str, JsonValue]]:
    found: dict[str, dict[str, JsonValue]] = {}
    for case, digest in picked(bench, cases, schema).items():
        if digest is None:
            continue
        match resolve(bench.store.get, digest, Expectation).data:
            case dict() as data:
                found[case] = data
            case _:
                pass
    return found


@dataclass(frozen=True)
class _Head:
    thread: int
    id: int


# Policy: each version is the one before with its temperature drawn again, a change an
# experimenter makes often and which leaves the rest as it was, and is drawn a mean
# quality its answers are drawn around, so that some fare better.
def _versions(
    bench: Bench, rng: random.Random, variation: TriedVariation, count: int
) -> list[tuple[_Head, float]]:
    edit = variation.configuration
    made = [(_Head(edit.thread, edit.id), rng.gauss(0.6, 0.15))]
    recipe = variation.recipe
    if recipe is None:
        return made
    while len(made) < count:
        before = resolve(bench.store.get, recipe.sampling, Sampling)
        drawn = round(rng.uniform(0.2, 1.0), 2)
        if drawn == before.temperature:
            continue
        sampling = Sampling.model_validate(
            {**before.model_dump(exclude={"kind"}), "temperature": drawn}
        )
        saved = bench.compose(edit.thread, made[-1][0].id, {"sampling": sampling})
        made.append((_Head(edit.thread, saved.edit.id), rng.gauss(0.6, 0.18)))
        recipe = bench.variation(edit.thread, {}, saved.edit.id).recipe
        assert recipe is not None
    return made


# Policy: the versions in the order they were saved, a few gatherings each, with now and
# then an earlier one gone back to.
def _order(rng: random.Random, versions: int, gatherings: int) -> list[int]:
    found: list[int] = []
    for n in range(gatherings):
        reached = min(versions - 1, n * versions // gatherings)
        found.append(rng.randrange(reached + 1) if rng.random() < 0.15 else reached)
    return found


# Policy: a version's first gathering is its baseline, where the World names one, and
# after it reviews of a case twice as often as tries.
def _sort(rng: random.Random, gathered: bool, based: bool) -> Sort:
    if not gathered and based:
        return "baseline"
    match rng.randrange(6):
        case 0 if based:
            return "baseline"
        case 1 | 2:
            return "try"
        case _:
            return "review"


# Duplication: src/chatddx/portal/mending.py:mend starts a gathering alike.
def _gather(
    bench: Bench,
    variation: TriedVariation,
    p: Placed,
    fakes: dict[str, Served],
    cases: list[str],
    seedings: tuple[Seeding, ...],
    rng: random.Random,
    qualities: dict[str, Quality],
    breaking: bool,
    leaving: bool,
) -> bool:
    first: UUID | None = None
    drawn: dict[str, tuple[int, ...]] = {}
    for s in seedings:
        each = drawn[s.name] = (
            suggest_seeds(s.seeds)
            if s.repeats is None
            else drawn[s.repeats][-s.seeds :]
        )
        with serving([p.fake]):
            try:
                started = bench.start(
                    variation,
                    p.endpoint,
                    cases,
                    each,
                    execution=_ONE_BY_ONE,
                    joining=first,
                )
            except (Invalid, Refused):
                break
        for _, running in started.runs:
            first = first or running.started.run
            trial = resolve(bench.store.get, running.started.trial, Trial)
            turns = [
                turn(bench, running, rng, qualities[case], hang_up=breaking and i == 0)
                for i, (case, _) in enumerate(
                    _ONE_BY_ONE.schedule(trial.cases, len(trial.seeds))
                )
            ]
            breaking = False
            finish = not (leaving and s is seedings[-1])
            send(bench, p.fake, fakes, running, turns, finish)
            leaving = leaving and finish
    return first is not None
