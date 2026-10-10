from typing import Literal

from chatddx.factors.request import Skeleton
from chatddx.ledger import RunItem
from chatddx.runner.send import STOPPED
from chatddx.scorers.answer import read

type Outcome = Literal["stopped", "errored", "unread", "completed", "invalid", "valid"]


# How an item ended, by its last call, and why when there is something to say. Without
# an answer it was stopped, errored or is unread; with one, it is completed when the
# output has no schema, else valid or invalid by it.
def outcome(skeleton: Skeleton, item: RunItem) -> tuple[Outcome, str | None]:
    last = item.calls[-1]
    answer = read(skeleton, last.response)
    if last.error == STOPPED:
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


# The prompt and completion tokens of an item's calls, as their responses count them.
def usage(item: RunItem) -> tuple[int, int]:
    used = [
        u
        for call in item.calls
        if call.response is not None
        and isinstance(u := call.response.get("usage"), dict)
    ]
    return (
        sum(n for u in used if isinstance(n := u.get("prompt_tokens"), int)),
        sum(n for u in used if isinstance(n := u.get("completion_tokens"), int)),
    )
