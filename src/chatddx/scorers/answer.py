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
_LITERAL = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null")
_PARTIAL = re.compile(
    r"-?\d*\.?\d*(?:[eE][+-]?\d*)?|t(?:r(?:ue?)?)?|f(?:a(?:l(?:se?)?)?)?|n(?:u(?:ll?)?)?"
)
_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
_ESCAPE = re.compile(r"\\(?:u[0-9a-fA-F]{0,3})?$")


class Answer(NamedTuple):
    value: JsonValue | None
    problem: str | None = None
    salvaged: bool = False


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
            found = _json(called[-1].arguments, "the answer tool's arguments", True)
        case NativeOutput():
            if not isinstance(content, str):
                return Answer(None, "no content")
            found = _json(content, "the content", True)
        case TextOutput():
            if not isinstance(content, str) or not content.strip():
                return Answer(None, "no content")
            if skeleton.output_schema is None:
                return Answer(content)
            found = _embedded(content)
    schema = skeleton.output_schema
    if found.value is None or not isinstance(schema, dict):
        return found
    return Answer(found.value, _breaks(schema, found.value), found.salvaged)


def _message(response: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    match response.get("choices"):
        case [{"message": dict() as message}, *_]:
            return message
        case _:
            return {}


def _json(text: str, what: str, salvage: bool = False) -> Answer:
    try:
        value: JsonValue = json.loads(text)
    except ValueError as e:
        closed = _closed(text) if salvage else None
        try:
            return Answer(json.loads(closed or ""), salvaged=True)
        except ValueError:
            return Answer(None, f"{what} isn't JSON: {e}")
    return Answer(value) if value is not None else Answer(None, f"{what} is null")


def _closed(text: str) -> str | None:
    opened: list[str] = []
    expect: list[str] = []
    cut: tuple[int, tuple[str, ...]] | None = None
    at = 0
    while at < len(text):
        c = text[at]
        if c.isspace():
            at += 1
        elif c in "{[":
            if opened and expect[-1] != "value" or not opened and cut is not None:
                return None
            opened.append(c)
            expect.append("key" if c == "{" else "value")
            at += 1
            cut = (at, tuple(opened))
        elif c in "}]":
            if not opened or "{[".index(opened[-1]) != "}]".index(c):
                return None
            _ = opened.pop(), expect.pop()
            at += 1
            if not opened:
                return None
            expect[-1] = "comma"
            cut = (at, tuple(opened))
        elif c == '"':
            if not opened or expect[-1] not in ("key", "value"):
                return None
            string = _STRING.match(text, at)
            if string is None:
                if expect[-1] == "key":
                    break
                kept = _ESCAPE.sub("", text[at:])
                return text[:at] + kept + '"' + _closers(opened)
            at = string.end()
            if expect[-1] == "key":
                expect[-1] = "colon"
            else:
                expect[-1] = "comma"
                cut = (at, tuple(opened))
        elif c in ":," and opened and expect[-1] == ("colon" if c == ":" else "comma"):
            expect[-1] = "value" if c == ":" or opened[-1] == "[" else "key"
            at += 1
        elif (literal := _LITERAL.match(text, at)) and opened and expect[-1] == "value":
            at = literal.end()
            expect[-1] = "comma"
            cut = (at, tuple(opened))
        elif _PARTIAL.fullmatch(text[at:].rstrip()):
            break
        else:
            return None
    if cut is None:
        return None
    end, held = cut
    return text[:end] + _closers(list(held))


def _closers(opened: list[str]) -> str:
    return "".join("}" if b == "{" else "]" for b in reversed(opened))


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
