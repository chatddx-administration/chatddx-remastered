from collections.abc import Callable, Mapping

from pydantic import JsonValue

from chatddx.factors.request import Skeleton, Slot, SlotName
from chatddx.factors.scoring import Judge, View
from chatddx.factors.select import select

from .scorer import (
    NO_ANSWER,
    NO_TARGET,
    Explained,
    Metric,
    Pick,
    Scored,
    Verdicts,
    explaining,
)

_AT: dict[str, JsonValue] = {
    "type": "string",
    "description": "A JSON Pointer to the value in each verdict",
}


def _scored(
    verdicts: Verdicts | None, at: str, value: Callable[[JsonValue], float | None]
) -> Explained:
    assert verdicts is not None
    seeds: list[float | None] = []
    picks: list[Pick | None] = []
    for verdict in verdicts:
        picked = None if verdict is None else select(verdict, at)
        counted = value(picked[0]) if picked else None
        seeds.append(counted)
        picks.append(
            None
            if verdict is None
            else Pick(at, picked[0] if picked else None, counted)
        )
    read = [v for v in seeds if v is not None]
    detail: dict[str, JsonValue] = {"seeds": list(seeds)}
    if not read:
        scored = Scored(None, detail | {"reason": "no seed gave a verdict"})
    else:
        scored = Scored(sum(read) / len(read), detail)
    return Explained(scored, picks=tuple(picks))


def _verdict(
    _output: list[JsonValue] | None,
    _expected: list[JsonValue],
    params: Mapping[str, JsonValue],
    verdicts: Verdicts | None,
) -> Explained:
    def held(value: JsonValue) -> float | None:
        return float(value) if isinstance(value, bool) else None

    return _scored(verdicts, str(params["at"]), held)


def _points(
    _output: list[JsonValue] | None,
    _expected: list[JsonValue],
    params: Mapping[str, JsonValue],
    verdicts: Verdicts | None,
) -> Explained:
    top = params["max"]
    assert isinstance(top, int | float)

    def share(value: JsonValue) -> float | None:
        if isinstance(value, bool) or not isinstance(value, int | float):
            return None
        return value / top

    return _scored(verdicts, str(params["at"]), share)


METRICS: dict[str, Metric] = {
    "verdict": explaining(
        "the share of the judge's seeds whose verdict holds true at `at`",
        _verdict,
        {
            "type": "object",
            "properties": {"at": _AT},
            "required": ["at"],
            "additionalProperties": False,
        },
        judged=True,
    ),
    "points": explaining(
        "the mean over the judge's seeds of the number at `at`, over `max`",
        _points,
        {
            "type": "object",
            "properties": {"at": _AT, "max": {"type": "number", "exclusiveMinimum": 0}},
            "required": ["at", "max"],
            "additionalProperties": False,
        },
        judged=True,
    ),
}


def asked(
    judge: Judge,
    skeleton: Skeleton,
    view: View,
    answer: JsonValue | None,
    expectation: JsonValue,
) -> dict[SlotName, str] | Scored:
    slots = {
        s.slot for m in skeleton.messages for s in m.content if isinstance(s, Slot)
    }
    if "expectation" in slots and not view.expectation_items(expectation):
        return Scored(None, NO_TARGET)
    if answer is None:
        return Scored(None, NO_ANSWER)
    if not view.output_items(answer):
        return Scored(None, {"reason": "nothing in the answer to judge"})
    return judge.fills(view, answer, expectation)
