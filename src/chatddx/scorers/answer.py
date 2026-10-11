import json
import re
from collections.abc import Mapping
from typing import NamedTuple

from jsonschema import validators
from jsonschema.exceptions import relevance
from pydantic import JsonValue
from referencing.exceptions import Unresolvable

from chatddx.factors.request import (
    NativeOutput,
    Skeleton,
    TextOutput,
    ToolOutput,
    tool_calls,
)

_FENCED = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)


class Answer(NamedTuple):
    value: JsonValue | None
    problem: str | None = None


def read(skeleton: Skeleton, response: Mapping[str, JsonValue] | None) -> Answer:
    if response is None:
        return Answer(None, "no response")
    message = _message(response)
    content = message.get("content")
    match skeleton.contract:
        case ToolOutput(name=name):
            called = [c for c in tool_calls(response) if c.name == name]
            if not called:
                return Answer(None, f"no call to the answer tool {name!r}")
            found = _json(called[-1].arguments, "the answer tool's arguments")
        case NativeOutput():
            if not isinstance(content, str):
                return Answer(None, "no content")
            found = _json(content, "the content")
        case TextOutput():
            if not isinstance(content, str) or not content.strip():
                return Answer(None, "no content")
            if skeleton.output_schema is None:
                return Answer(content)
            found = _embedded(content)
    schema = skeleton.output_schema
    if found.value is None or not isinstance(schema, dict):
        return found
    return Answer(found.value, _breaks(schema, found.value))


def _message(response: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    match response.get("choices"):
        case [{"message": dict() as message}, *_]:
            return message
        case _:
            return {}


def _json(text: str, what: str) -> Answer:
    try:
        value: JsonValue = json.loads(text)
    except ValueError as e:
        return Answer(None, f"{what} isn't JSON: {e}")
    return Answer(value) if value is not None else Answer(None, f"{what} is null")


def _embedded(text: str) -> Answer:
    whole = _json(text.strip(), "the content")
    if whole.value is not None:
        return whole
    for block in reversed(_FENCED.findall(text)):
        fenced = _json(block.strip(), "a fenced block")
        if fenced.value is not None:
            return fenced
    decoder = json.JSONDecoder()
    last: JsonValue | None = None
    at = 0
    while (start := _next_open(text, at)) is not None:
        try:
            value, end = decoder.raw_decode(text, start)
        except ValueError:
            at = start + 1
            continue
        last, at = value, end
    if last is None:
        return Answer(None, "no JSON in the content")
    return Answer(last)


def _next_open(text: str, at: int) -> int | None:
    found = [i for i in (text.find("{", at), text.find("[", at)) if i != -1]
    return min(found) if found else None


def _breaks(schema: dict[str, JsonValue], value: JsonValue) -> str | None:
    check = validators.validator_for(schema)(schema)
    try:
        error = max(check.iter_errors(value), key=relevance, default=None)
    except Unresolvable as e:
        return f"the output schema can't be checked: {e.ref} can't be resolved"
    if error is None:
        return None
    where = "/".join(str(p) for p in error.absolute_path)
    return f"at /{where}: {error.message}" if where else f"at the root: {error.message}"
