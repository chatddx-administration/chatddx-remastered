from collections.abc import Mapping
from typing import Literal, NamedTuple

from pydantic import JsonValue

from .base import Frozen

# Accommodating for servers: vLLM 0.24 says `reasoning`, as the fake does; other
# OpenAI-compatible servers say `reasoning_content`.
REASONING = ("reasoning", "reasoning_content")


class ToolCall(Frozen):
    id: str
    name: str
    arguments: str


class Part(NamedTuple):
    kind: Literal["reasoning", "content", "tool_call"]
    text: str
    name: str | None = None


def choice(response: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    match response.get("choices"):
        case [dict() as first, *_]:
            return first
        case _:
            return {}


def message(response: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    match choice(response).get("message"):
        case dict() as found:
            return found
        case _:
            return {}


def reasoning(said: Mapping[str, JsonValue]) -> str | None:
    for key in REASONING:
        if isinstance(text := said.get(key), str) and text:
            return text
    return None


def tool_calls(response: Mapping[str, JsonValue]) -> tuple[ToolCall, ...]:
    calls = message(response).get("tool_calls")
    found: list[ToolCall] = []
    for call in calls if isinstance(calls, list) else []:
        match call:
            case {
                "id": str() as id,
                "function": {"name": str() as name, "arguments": str() as arguments},
            }:
                found.append(ToolCall(id=id, name=name, arguments=arguments))
            case _:
                pass
    return tuple(found)


def parts(response: Mapping[str, JsonValue]) -> list[Part]:
    said = message(response)
    found: list[Part] = []
    if (thought := reasoning(said)) is not None:
        found.append(Part("reasoning", thought))
    if isinstance(content := said.get("content"), str) and content:
        found.append(Part("content", content))
    found.extend(Part("tool_call", c.arguments, c.name) for c in tool_calls(response))
    return found
