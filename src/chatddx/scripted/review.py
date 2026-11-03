import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest import mock

from pydantic import JsonValue

from chatddx import settings
from chatddx.bench import Bench
from chatddx.bench.seen import choices, picked
from chatddx.catalog import threads
from chatddx.factors.base import Invalid, resolve
from chatddx.factors.gathering import REVIEW
from chatddx.factors.scoring import Expectation
from chatddx.factors.trial import suggest_seeds
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.runner import Refused
from chatddx.scorers.patterns import Pattern

from .answering import (
    FIELDS,
    Placed,
    Quality,
    clock,
    pattern_of,
    placing,
    send,
    turn,
)
from .fakes import standing_in


@dataclass(frozen=True)
class Reviewed:
    gatherings: int
    versions: int
    broken: int
    unfinished: int
    skipped: dict[str, str]


def review(
    bench: Bench,
    case: str,
    schema: str,
    *,
    gatherings: int = 40,
    versions: int = 12,
    seed: int = 1,
    days: int = 42,
) -> Reviewed:
    """Writes a review's worth of the case for the person: their expectation of it under
    the schema in `versions` versions, and `gatherings` evaluations of it, as Run starts
    them, spread over the last `days` days, each scored against one of the versions and
    answered by the fake vLLM as well as a quality drawn for its version has it. A few
    are broken by a server that hangs up, or left with a run unfinished.

    Sends and scores every run in the calling thread, serving each one's fakes the while,
    on ports of this machine's for endpoints the fake vLLM doesn't run; lifts the
    person's quota of runs for as long.

    Heads-up: `LookupError` when no configuration of the person's can run the case."""
    rng = random.Random(seed)
    standing, fakes, refused = standing_in(bench.inventory, bench.store.get)
    bench = Bench(bench.conn, bench.person, standing)
    placed, skipped = placing(bench, fakes, refused)
    if not placed:
        said = "; ".join(f"{n}: {why}" for n, why in skipped.items()) or "it has none"
        raise LookupError(
            f"no configuration of {bench.person.login}'s can run {bench.title(case)}: "
            + said
        )
    base = _base(bench, case, schema)
    pool = _pool(bench, schema)
    made = _versions(rng, base, pool, versions)
    thread, head = _own(bench, case, schema, base)
    order = _order(rng, len(made), gatherings)
    start = datetime.now(UTC) - timedelta(days=days)
    step = timedelta(days=days) / gatherings
    gathered = broken = unfinished = 0
    with mock.patch.object(settings, "RUNS_PER_DAY", 1 << 30):
        for n, at in enumerate(order):
            version = made[at]
            head = _expect(bench, thread, head, case, schema, version.data)
            fault = rng.random()
            breaking = fault < 0.06
            leaving = 0.06 <= fault < 0.1
            when = start + step * n + timedelta(minutes=rng.randrange(0, 600))
            with clock(when):
                ran = _gather(
                    bench, case, rng, version, placed, fakes, breaking, leaving
                )
            gathered += ran
            broken += ran and breaking
            unfinished += ran and leaving
    return Reviewed(gathered, len(made), broken, unfinished, skipped)


def _base(bench: Bench, case: str, schema: str) -> dict[str, JsonValue]:
    digest = picked(bench, [case], schema)[case]
    if digest is None:
        raise LookupError(f"{bench.title(case)} has no expectation under {schema}")
    match resolve(bench.store.get, digest, Expectation).data:
        case dict() as data:
            return data
        case _:
            raise LookupError(f"{bench.title(case)}'s expectation isn't an object")


def _pool(bench: Bench, schema: str) -> dict[str, list[str]]:
    cases = [c for f in bench.families() for c in f.cases]
    found: dict[str, list[str]] = {f: [] for f in FIELDS}
    for digest in picked(bench, cases, schema).values():
        if digest is None:
            continue
        data = resolve(bench.store.get, digest, Expectation).data
        for f in FIELDS:
            if (pattern := pattern_of(data, f)) is not None and pattern not in found[f]:
                found[f].append(pattern)
    return found


# Policy: each version is the one before changed in one way an expert might change it,
# and is drawn a mean quality its answers are drawn around, so that some fare better.
def _versions(
    rng: random.Random,
    base: dict[str, JsonValue],
    pool: dict[str, list[str]],
    count: int,
) -> list[Quality]:
    made = [Quality(base, rng.gauss(0.6, 0.15))]
    while len(made) < count:
        data = _changed(rng, made[-1].data, pool)
        if data == made[-1].data:
            continue
        mean = made[-1].mean if _worded(data, made[-1].data) else rng.gauss(0.6, 0.18)
        made.append(Quality(data, mean))
    return made


def _changed(
    rng: random.Random, data: dict[str, JsonValue], pool: dict[str, list[str]]
) -> dict[str, JsonValue]:
    held: dict[str, Any] = json.loads(json.dumps(data))
    field = rng.choice([f for f in FIELDS if pool[f] or f in held])
    target: Any = held.get(field)
    match rng.randrange(5):
        case 0 if isinstance(target, dict) and "pattern" in target:
            others = [p for p in pool[field] if p != target["pattern"]]
            if others:
                target["pattern"] = f"{target['pattern']} | {rng.choice(others)}"
        case 1 if (was := pattern_of(cast(JsonValue, target), "")) and _readable(
            narrowed := was.split(" | ")[0]
        ):
            target["pattern"] = narrowed
        case 2 if pool[field]:
            held[field] = {**(target if isinstance(target, dict) else {})}
            held[field]["pattern"] = rng.choice(pool[field])
        case 3 if field == "warning":
            held[field] = False if target is not False else {"pattern": "shock"}
        case 3 if field == "dont_miss" and field in held:
            del held[field]
        case _ if isinstance(target, dict):
            target["text"] = rng.choice(_NOTES)
        case _:
            pass
    return held


def _readable(pattern: str) -> bool:
    try:
        _ = Pattern(pattern)
    except Invalid:
        return False
    return True


_NOTES = (
    "The likeliest, given the history.",
    "Named as the clinician would name it.",
    "What the vignette points to before any test.",
    "As the department's guideline words it.",
)


def _worded(data: dict[str, JsonValue], before: dict[str, JsonValue]) -> bool:
    return all(pattern_of(data, f) == pattern_of(before, f) for f in FIELDS) and (
        data.get("warning") is False
    ) == (before.get("warning") is False)


# Policy: the versions in the order they were written, a gathering or more each, with
# now and then an earlier one gone back to.
def _order(rng: random.Random, versions: int, gatherings: int) -> list[int]:
    found: list[int] = []
    for n in range(gatherings):
        reached = min(versions - 1, n * versions // gatherings)
        found.append(rng.randrange(reached + 1) if rng.random() < 0.15 else reached)
    return found


def _own(
    bench: Bench, case: str, schema: str, base: dict[str, JsonValue]
) -> tuple[int, int]:
    held = choices(bench, [case], schema)[case]
    if held:
        thread = min(held)
        return thread, threads.head(bench.rows, thread).id
    made = bench.new(
        Expectation(case=case, expectation_schema=schema, data=base), None
    ).edit
    return made.thread, made.id


def _expect(
    bench: Bench,
    thread: int,
    head: int,
    case: str,
    schema: str,
    data: dict[str, JsonValue],
) -> int:
    held = Expectation(case=case, expectation_schema=schema, data=data)
    return bench.edit(thread, head, held).edit.id


# Duplication: src/chatddx/portal/review.py:running_in_review starts an evaluation alike.
def _gather(
    bench: Bench,
    case: str,
    rng: random.Random,
    version: Quality,
    placed: list[Placed],
    fakes: dict[str, Served],
    breaking: bool,
    leaving: bool,
) -> bool:
    first = None
    broke = breaking
    left = leaving
    for p in placed:
        drawn: dict[str, tuple[int, ...]] = {}
        for s in REVIEW:
            each = drawn[s.name] = (
                suggest_seeds(s.seeds)
                if s.repeats is None
                else drawn[s.repeats][-s.seeds :]
            )
            with serving([p.fake]):
                try:
                    started = bench.start(
                        p.variation, p.endpoint, [case], each, joining=first
                    )
                except (Invalid, Refused):
                    break
            for _, running in started.runs:
                first = first or running.started.run
                turns = [
                    turn(bench, running, rng, version, hang_up=broke and i == 0)
                    for i in range(len(each))
                ]
                broke = False
                finish = not (left and s.repeats)
                send(bench, p.fake, fakes, running, turns, finish)
                if left and s.repeats:
                    left = False
    return first is not None
