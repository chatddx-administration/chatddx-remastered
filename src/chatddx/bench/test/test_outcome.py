import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import JsonValue

from chatddx.bench import outcome, usage
from chatddx.curation import Plan
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.request import Skeleton
from chatddx.fake_vllm.chat import instance
from chatddx.ledger import Call, ItemKey, RunItem, ToolRun, Turn
from chatddx.runner.send import STOPPED
from chatddx.test.world import LINES, NATIVE

pytestmark = pytest.mark.wip

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def skeleton(plan: Plan, recipe: str) -> Skeleton:
    return resolve(plan.registry.get, plan.named("recipe", recipe).digest, Skeleton)


def call(
    content: str | None = None,
    error: str | None = None,
    tokens: tuple[int, int] = (0, 0),
) -> Call:
    message: JsonValue = {"role": "assistant", "content": content}
    used: JsonValue = {"prompt_tokens": tokens[0], "completion_tokens": tokens[1]}
    return Call(
        request=Fingerprint.of(b"request"),
        started_at=NOW,
        finished_at=NOW,
        response=None
        if content is None
        else {"choices": [{"index": 0, "message": message}], "usage": used},
        error=error,
    )


def item(*calls: Call) -> RunItem:
    first, *rest = calls
    ran = ToolRun(id="t", name="lookup", started_at=NOW, finished_at=NOW, result="")
    return RunItem(
        run=uuid4(),
        key=ItemKey(case="sha256:" + "0" * 64, replicate=0),
        vignette=Fingerprint.of(b"vignette"),
        call=first,
        turns=tuple(Turn(tools=(ran,), call=c) for c in rest),
    )


def test_an_item_ends_by_its_last_call_and_the_skeleton_s_output(plan: Plan) -> None:
    lines, native = skeleton(plan, LINES), skeleton(plan, NATIVE)
    document: JsonValue = instance(native.output_schema)
    assert isinstance(document, dict)
    broken = {**document, "diagnoses": "sepsis"}

    assert outcome(lines, item(call("Sepsis"))) == ("completed", None)
    assert outcome(native, item(call(json.dumps(document)))) == ("valid", None)
    assert outcome(native, item(call(json.dumps(broken)))) == (
        "invalid",
        "at /diagnoses: 'sepsis' is not of type 'array'",
    )
    assert outcome(lines, item(call(None, "HTTP 500"))) == ("errored", "HTTP 500")
    assert outcome(lines, item(call("  "))) == ("unread", "no content")
    assert outcome(lines, item(call("Sep", STOPPED))) == ("stopped", None)
    assert outcome(lines, item(call(None, "HTTP 500"), call("Sepsis"))) == (
        "completed",
        None,
    )


def test_an_item_s_usage_counts_every_call() -> None:
    assert usage(item(call("a", tokens=(10, 2)), call("b", tokens=(14, 3)))) == (24, 5)
    assert usage(item(call(None, "HTTP 500"))) == (0, 0)
