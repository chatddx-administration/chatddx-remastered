import json
import random
from collections.abc import Callable, Generator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, cast
from unittest import mock

from pydantic import JsonValue

from chatddx.api import threads as api
from chatddx.bench import Bench, TriedVariation
from chatddx.factors.base import Invalid, resolve
from chatddx.factors.request import Skeleton, ToolOutput
from chatddx.factors.trial import Trial
from chatddx.fake_vllm.chat import instance
from chatddx.fake_vllm.script import Script, Turn
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.runner import Running
from chatddx.scorers.patterns import Pattern

from .fakes import canaried
from .run import judging

# Dependency: each module of the runner that stamps what it records with the time.
_CLOCKS = (
    "chatddx.runner.run._now",
    "chatddx.runner.rounds._now",
    "chatddx.runner.send._now",
    "chatddx.runner.score._now",
)
FIELDS = ("diagnosis", "warning", "disposition", "dont_miss")
_OUTLIERS = 0.08
_SPREAD = 0.12


@dataclass(frozen=True)
class Placed:
    variation: TriedVariation
    endpoint: str
    fake: Served


@dataclass(frozen=True)
class Quality:
    data: dict[str, JsonValue]
    mean: float


# Policy: the person's configurations as Run takes them, each with the fake that serves
# its endpoint, and why each other one is left out.
def placing(
    bench: Bench, fakes: dict[str, Served], refused: dict[str, str]
) -> tuple[list[Placed], dict[str, str]]:
    login = bench.person.login
    found = api.threads(bench, "configuration", purpose="generation", owner=login)
    placed: list[Placed] = []
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
        placed.append(Placed(variation, at.name, fakes[at.name]))
    return placed, skipped


def pattern_of(data: JsonValue, field: str) -> str | None:
    match data:
        case {"pattern": str() as pattern} if field == "":
            return pattern
        case dict() if field:
            return pattern_of(cast(dict[str, JsonValue], data).get(field), "")
        case _:
            return None


@contextmanager
def clock(at: datetime) -> Generator[None]:
    ticks = iter(range(1 << 30))

    def now() -> datetime:
        return at + timedelta(milliseconds=next(ticks))

    with ExitStack() as stack:
        for where in _CLOCKS:
            _ = stack.enter_context(mock.patch(where, now))
        yield


def send(
    bench: Bench,
    fake: Served,
    fakes: dict[str, Served],
    running: Running,
    turns: list[Turn],
    finish: bool,
) -> None:
    unscripted = canaried(bench.store.get, running.started.canaries)
    with serving([fake], script=Script(turns, unscripted)):
        running.send(lambda _: None)
    if not finish:
        return
    _ = running.finish()
    with judging(bench, running.started, fakes):
        _ = bench.score(running.started)


def turn(
    bench: Bench,
    running: Running,
    rng: random.Random,
    version: Quality,
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
def _answer(rng: random.Random, version: Quality) -> dict[str, Any]:
    quality = (
        rng.random()
        if rng.random() < _OUTLIERS
        else min(1.0, max(0.0, rng.gauss(version.mean, _SPREAD)))
    )
    pick: Callable[[int], int] = rng.randrange
    named = {
        f: Pattern(p).example(pick).capitalize()
        for f in FIELDS
        if (p := pattern_of(version.data, f)) is not None
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
