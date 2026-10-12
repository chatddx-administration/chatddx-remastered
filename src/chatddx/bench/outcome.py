from typing import Literal

from pydantic import JsonValue

from chatddx.factors.request import Skeleton
from chatddx.ledger import RunItem
from chatddx.runner.send import STOPPED
from chatddx.scorers.answer import read

type Outcome = Literal["stopped", "errored", "unread", "completed", "invalid", "valid"]


def outcome(skeleton: Skeleton, item: RunItem) -> tuple[Outcome, str | None]:
    last = item.calls[-1]
    answer = read(skeleton, last.response)
    unsent = bool(item.turns) and item.turns[-1].call is None
    if last.error == STOPPED or unsent:
        return "stopped", None
    if answer.value is None:
        if last.error is not None:
            return "errored", last.error
        return "unread", answer.problem
    if skeleton.output_schema is None:
        return "completed", last.error
    if answer.problem is not None:
        return "invalid", last.error or answer.problem
    return "valid", last.error


def usage(item: RunItem) -> tuple[int, int]:
    prompt = completion = 0
    for call in item.calls:
        response = call.response or {}
        match response.get("usage"):
            case dict() as used:
                if isinstance(n := used.get("prompt_tokens"), int):
                    prompt += n
                if isinstance(n := used.get("completion_tokens"), int):
                    completion += n
            case _:
                completion += _streamed(response)
    return prompt, completion


# A stream cut short ends before its usage, but its choice holds the token ids it streamed.
def _streamed(response: dict[str, JsonValue]) -> int:
    match response.get("choices"):
        case [{"token_ids": list() as ids}, *_]:
            return len(ids)
        case _:
            return 0
