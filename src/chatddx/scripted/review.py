import json
import random
from collections.abc import Callable, Generator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest import mock

from pydantic import JsonValue

from chatddx import settings
from chatddx.api import threads as api
from chatddx.bench import Bench, TriedVariation
from chatddx.bench.seen import choices, picked
from chatddx.catalog import threads
from chatddx.factors.base import Invalid, resolve
from chatddx.factors.gathering import REPLICATED
from chatddx.factors.request import Skeleton, ToolOutput
from chatddx.factors.scoring import Expectation
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.fake_vllm.chat import instance
from chatddx.fake_vllm.script import Script, Turn
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.runner import Refused, Running
from chatddx.scorers.patterns import Pattern

from .fakes import standing_in
from .run import judging

# Dependency: each module of the runner that stamps what it records with the time.
_CLOCKS = (
    "chatddx.runner.run._now",
    "chatddx.runner.rounds._now",
    "chatddx.runner.send._now",
    "chatddx.runner.score._now",
)
_FIELDS = ("diagnosis", "warning", "disposition", "dont_miss")
_OUTLIERS = 0.08
_SPREAD = 0.12


@dataclass(frozen=True)
class Reviewed:
    gatherings: int
    versions: int
    broken: int
    unfinished: int
    skipped: dict[str, str]


@dataclass(frozen=True)
class _Placed:
    variation: TriedVariation
    endpoint: str
    fake: Served


@dataclass(frozen=True)
class _Version:
    data: dict[str, JsonValue]
    mean: float


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
    placed, skipped = _placed(bench, fakes, refused)
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
            with _clock(when):
                ran = _gather(
                    bench, case, rng, version, placed, fakes, breaking, leaving
                )
            gathered += ran
            broken += ran and breaking
            unfinished += ran and leaving
    return Reviewed(gathered, len(made), broken, unfinished, skipped)


# Policy: the person's configurations as Run takes them, each with the fake that serves
# its endpoint, and why each other one is left out.
def _placed(
    bench: Bench, fakes: dict[str, Served], refused: dict[str, str]
) -> tuple[list[_Placed], dict[str, str]]:
    login = bench.person.login
    found = api.threads(bench, "configuration", purpose="generation", owner=login)
    placed: list[_Placed] = []
    skipped: dict[str, str] = {}
    for t in sorted(found, key=lambda t: t.name or t.title):
        name = t.name or t.title
        if t.outdated:
            skipped[name] = "it is out of date"
            continue
        try:
            variation = bench.variation(t.id, {}, None)
            at = bench.at(variation)
        except (Invalid, LookupError) as e:
            skipped[name] = str(e)
            continue
        if at.name not in fakes:
            skipped[name] = refused.get(at.name, f"no fake serves {at.name}")
            continue
        placed.append(_Placed(variation, at.name, fakes[at.name]))
    return placed, skipped


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
    found: dict[str, list[str]] = {f: [] for f in _FIELDS}
    for digest in picked(bench, cases, schema).values():
        if digest is None:
            continue
        data = resolve(bench.store.get, digest, Expectation).data
        for f in _FIELDS:
            if (pattern := _pattern(data, f)) is not None and pattern not in found[f]:
                found[f].append(pattern)
    return found


def _pattern(data: JsonValue, field: str) -> str | None:
    match data:
        case {"pattern": str() as pattern} if field == "":
            return pattern
        case dict() if field:
            return _pattern(cast(dict[str, JsonValue], data).get(field), "")
        case _:
            return None


# Policy: each version is the one before changed in one way an expert might change it,
# and is drawn a mean quality its answers are drawn around, so that some fare better.
def _versions(
    rng: random.Random,
    base: dict[str, JsonValue],
    pool: dict[str, list[str]],
    count: int,
) -> list[_Version]:
    made = [_Version(base, rng.gauss(0.6, 0.15))]
    while len(made) < count:
        data = _changed(rng, made[-1].data, pool)
        if data == made[-1].data:
            continue
        mean = made[-1].mean if _worded(data, made[-1].data) else rng.gauss(0.6, 0.18)
        made.append(_Version(data, mean))
    return made


def _changed(
    rng: random.Random, data: dict[str, JsonValue], pool: dict[str, list[str]]
) -> dict[str, JsonValue]:
    held: dict[str, Any] = json.loads(json.dumps(data))
    field = rng.choice([f for f in _FIELDS if pool[f] or f in held])
    target: Any = held.get(field)
    match rng.randrange(5):
        case 0 if isinstance(target, dict) and "pattern" in target:
            others = [p for p in pool[field] if p != target["pattern"]]
            if others:
                target["pattern"] = f"{target['pattern']} | {rng.choice(others)}"
        case 1 if (was := _pattern(cast(JsonValue, target), "")) and _readable(
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
    return all(_pattern(data, f) == _pattern(before, f) for f in _FIELDS) and (
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


@contextmanager
def _clock(at: datetime) -> Generator[None]:
    ticks = iter(range(1 << 30))

    def now() -> datetime:
        return at + timedelta(milliseconds=next(ticks))

    with ExitStack() as stack:
        for where in _CLOCKS:
            _ = stack.enter_context(mock.patch(where, now))
        yield


# Duplication: src/chatddx/portal/review.py:running_in_review starts an evaluation alike.
def _gather(
    bench: Bench,
    case: str,
    rng: random.Random,
    version: _Version,
    placed: list[_Placed],
    fakes: dict[str, Served],
    breaking: bool,
    leaving: bool,
) -> bool:
    first = None
    broke = breaking
    left = leaving
    for p in placed:
        drawn: dict[str, tuple[int, ...]] = {}
        for s in REPLICATED:
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
                    _turn(bench, running, rng, version, hang_up=broke and i == 0)
                    for i in range(len(each))
                ]
                broke = False
                finish = not (left and s.repeats)
                _send(bench, p.fake, fakes, running, turns, finish)
                if left and s.repeats:
                    left = False
    return first is not None


def _send(
    bench: Bench,
    fake: Served,
    fakes: dict[str, Served],
    running: Running,
    turns: list[Turn],
    finish: bool,
) -> None:
    with serving([fake], script=Script(turns)):
        running.send(lambda _: None)
    if not finish:
        return
    _ = running.finish()
    with judging(bench, running.started, fakes):
        _ = bench.score(running.started)


def _turn(
    bench: Bench,
    running: Running,
    rng: random.Random,
    version: _Version,
    hang_up: bool,
) -> Turn:
    trial = resolve(bench.store.get, running.started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    answer = _answer(rng, version)
    schema = skeleton.output_schema
    if schema is None:
        content = "\n".join(answer["diagnoses"])
        return Turn(content=content, hang_up=len(content) // 4 if hang_up else None)
    shaped = json.dumps(_shaped(schema, answer))
    if isinstance(skeleton.contract, ToolOutput):
        return Turn(calls=((skeleton.contract.name, shaped),))
    return Turn(content=shaped, hang_up=len(shaped) // 8 if hang_up else None)


# Policy: an answer as good as a quality drawn around its version's mean, with some
# outliers: the better, the higher the expected diagnosis and the likelier the rest named.
def _answer(rng: random.Random, version: _Version) -> dict[str, Any]:
    quality = (
        rng.random()
        if rng.random() < _OUTLIERS
        else min(1.0, max(0.0, rng.gauss(version.mean, _SPREAD)))
    )
    pick: Callable[[int], int] = rng.randrange
    named = {
        f: Pattern(p).example(pick).capitalize()
        for f in _FIELDS
        if (p := _pattern(version.data, f)) is not None
    }
    diagnoses: list[str] = rng.sample(list(_FILLER), 4)
    if "diagnosis" in named and rng.random() < quality * 1.2:
        diagnoses.insert(int((1 - quality) * rng.randrange(1, 5)), named["diagnosis"])
    critical = None
    if "dont_miss" in named and rng.random() < quality:
        critical = named["dont_miss"]
        diagnoses.append(critical)
    named_warning = "warning" in named and rng.random() < quality
    named_disposition = "disposition" in named and rng.random() < quality
    return {
        "diagnoses": diagnoses,
        "critical": critical,
        "warning": named["warning"] if named_warning else "None expected.",
        "disposition": named["disposition"] if named_disposition else "Reassess.",
    }


_FILLER = (
    "Gastroenteritis",
    "Musculoskeletal pain",
    "Anxiety",
    "Viral infection",
    "Medication side effect",
    "Dehydration",
    "Migraine",
    "Constipation",
)


def _shaped(schema: JsonValue, answer: dict[str, Any]) -> JsonValue:
    held: Any = instance(schema)
    if not isinstance(held, dict):
        return cast(JsonValue, held)
    shaped = cast(dict[str, Any], held)
    if isinstance(listed := shaped.get("diagnoses"), list):
        model: Any = cast(list[Any], listed)[0] if listed else None
        shaped["diagnoses"] = [
            {**model, "diagnosis": d, "critical": d == answer["critical"]}
            if isinstance(model, dict)
            else d
            for d in answer["diagnoses"]
        ]
    if "acute_warning" in shaped:
        shaped["acute_warning"] = answer["warning"]
    if isinstance(management := shaped.get("management"), dict):
        cast(dict[str, Any], management)["disposition"] = answer["disposition"]
    return shaped
