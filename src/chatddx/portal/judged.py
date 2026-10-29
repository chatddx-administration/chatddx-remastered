import json
from typing import NamedTuple

from pydantic import JsonValue

from chatddx.bench import Bench
from chatddx.factors.base import resolve
from chatddx.factors.engine import served_model_name
from chatddx.factors.request import Skeleton, SlotName
from chatddx.factors.scoring import Judge, Scoring, View
from chatddx.ledger import fingerprint_request
from chatddx.ledger.score import JudgeCall
from chatddx.scorers.answer import read
from chatddx.scorers.scorer import Pick, Scored, Verdicts
from chatddx.scorers.verdicts import asked

from .runs import worded_parts


class Field(NamedTuple):
    name: str
    about: str | None
    value: JsonValue
    picked: bool


class Seeded(NamedTuple):
    at: int
    seed: int
    rebuilt: bool
    status: int | None
    error: str | None
    parts: list[tuple[str, str, str]]
    verdict: JsonValue | None
    problem: str | None
    fields: list[Field] | None
    pick: Pick | None


class Judged(NamedTuple):
    judge: str
    fills: dict[SlotName, str] | None
    unasked: JsonValue
    messages: list[tuple[str, str]]
    seeds: list[Seeded]


def verdicts_of(bench: Bench, judge: str, calls: tuple[JudgeCall, ...]) -> Verdicts:
    skeleton = _skeleton(bench, judge)
    return [read(skeleton, c.call.response).value for c in calls]


def judged(
    bench: Bench,
    scoring: Scoring,
    view: View,
    by: str,
    calls: tuple[JudgeCall, ...],
    answer: JsonValue | None,
    data: JsonValue | None,
    picks: tuple[Pick | None, ...],
) -> Judged:
    judge = resolve(bench.store.get, by, Judge)
    skeleton = _skeleton(bench, by)
    fills = (
        Scored(None, {"reason": "no expectation for the case"})
        if data is None
        else asked(judge, skeleton, view, answer, data)
    )
    if isinstance(fills, Scored):
        return Judged(bench.title(by), None, fills.detail, [], [])
    model = served_model_name(scoring.engine_of(by), bench.store.get)
    messages: list[tuple[str, str]] = []
    seeds: list[Seeded] = []
    for n, made in enumerate(calls):
        seed = judge.seeds[made.seed_index]
        body = skeleton.render(model=model, seed=seed, fills=fills)
        if not messages:
            messages = _messages(body)
        response = made.call.response
        verdict = read(skeleton, response)
        pick = picks[n] if n < len(picks) else None
        seeds.append(
            Seeded(
                made.seed_index,
                seed,
                fingerprint_request(body) == made.call.request,
                made.call.status,
                made.call.error,
                [] if response is None else worded_parts(response),
                verdict.value,
                verdict.problem,
                _fields(skeleton.output_schema, verdict.value, pick),
                pick,
            )
        )
    return Judged(bench.title(by), fills, None, messages, seeds)


def _skeleton(bench: Bench, judge: str) -> Skeleton:
    held = resolve(bench.store.get, judge, Judge)
    return resolve(bench.store.get, held.skeleton, Skeleton)


def _messages(body: dict[str, JsonValue]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    held = body.get("messages")
    for message in held if isinstance(held, list) else []:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        shown = content if isinstance(content, str) else json.dumps(content, indent=2)
        found.append((str(message.get("role")), shown))
    return found


def _fields(
    schema: JsonValue, verdict: JsonValue | None, pick: Pick | None
) -> list[Field] | None:
    if not isinstance(verdict, dict):
        return None
    held = schema.get("properties") if isinstance(schema, dict) else None
    properties = held if isinstance(held, dict) else {}
    found: list[Field] = []
    for name, value in verdict.items():
        about = properties.get(name)
        described = about.get("description") if isinstance(about, dict) else None
        found.append(
            Field(
                name,
                described if isinstance(described, str) else None,
                value,
                pick is not None and pick.at == "/" + _escaped(name),
            )
        )
    return found


def _escaped(name: str) -> str:
    return name.replace("~", "~0").replace("/", "~1")
