import json
from datetime import UTC, datetime

import pytest
from jsonschema import validators
from pydantic import JsonValue

from chatddx.curation import Plan
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.request import (
    Compilation,
    Skeleton,
    Tool,
    Toolset,
    compile_request,
)
from chatddx.factors.response import ToolCall
from chatddx.ledger import Call
from chatddx.runner.rounds import Toolbox, load
from chatddx.runner.test import tools
from chatddx.test.world import LINES

FUNCTIONS = {"lookup": tools.lookup, "broken": tools.broken, "counted": tools.counted}


def toolbox() -> Toolbox:
    check = validators.validator_for(tools.PARAMETERS)(tools.PARAMETERS)
    return Toolbox(
        functions=FUNCTIONS,
        parameters={name: check for name in FUNCTIONS},
        answer="final_result",
        max_rounds=2,
        code=(),
    )


def called(name: str, arguments: object = None, raw: str | None = None) -> ToolCall:
    text = raw if raw is not None else json.dumps(arguments or {"query": "sepsis"})
    return ToolCall(id="call-1", name=name, arguments=text)


def failure(call: ToolCall) -> tuple[str | None, str]:
    ran = toolbox().run(call)
    assert ran.result == f"error: {ran.error}"
    return ran.error, ran.result


def test_a_tool_s_answer_is_its_result() -> None:
    ran = toolbox().run(called("lookup", {"query": "sepsis", "max_results": 3}))
    assert (ran.id, ran.name, ran.result, ran.error) == (
        "call-1",
        "lookup",
        "3 results for 'sepsis'",
        None,
    )
    assert ran.started_at <= ran.finished_at


def test_what_goes_wrong_is_told_to_the_model() -> None:
    assert failure(called("nowhere"))[0] == "no tool named 'nowhere'"
    error, _ = failure(called("lookup", raw="{query"))
    assert error is not None and error.startswith("the arguments aren't JSON: ")
    assert failure(called("lookup", raw='["sepsis"]'))[0] == (
        "the arguments aren't an object"
    )
    assert failure(called("lookup", {"max_results": 3}))[0] == (
        "the arguments don't fit the parameters: 'query' is a required property"
    )
    assert failure(called("broken"))[0] == "OSError: no answer for 'sepsis'"
    assert failure(called("counted"))[0] == "the tool returned int, not text"


def response(*names: str) -> Call:
    at = datetime.now(UTC)
    calls: list[JsonValue] = [
        {
            "id": f"call-{n}",
            "type": "function",
            "function": {"name": name, "arguments": "{}"},
        }
        for n, name in enumerate(names)
    ]
    message: JsonValue = {"role": "assistant", "content": None, "tool_calls": calls}
    return Call(
        request=Fingerprint.of(b"request"),
        started_at=at,
        finished_at=at,
        status=200,
        response={"choices": [{"index": 0, "message": message}]},
    )


def test_a_round_answers_every_call_until_the_answer_tool_is_called() -> None:
    box = toolbox()
    assert [c.name for c in box.pending(response("lookup", "broken"))] == [
        "lookup",
        "broken",
    ]
    assert box.pending(response("lookup", "final_result")) == ()
    assert box.pending(response()) == ()
    cut = response("lookup").model_copy(update={"error": "stopped"})
    assert box.pending(cut) == ()


def skeleton(plan: Plan, *made: Tool) -> tuple[Skeleton, Toolset]:
    named = plan.named("recipe", LINES)
    assert named.compilation is not None
    recipe = resolve(plan.registry.get, named.compilation, Compilation).recipe
    toolset = Toolset(tools=tuple(plan.registry.add(t) for t in made), max_rounds=3)
    with_tools = recipe.model_copy(update={"toolset": plan.registry.add(toolset)})
    facts = plan.facts.about(recipe.model, plan.registry.get)
    return compile_request(with_tools, plan.registry.get, facts), toolset


def test_tools_load_from_the_running_code_and_record_it(plan: Plan) -> None:
    made, toolset = skeleton(plan, tools.component("lookup"), tools.component("broken"))
    box = load(made, plan.registry.get)
    assert box is not None
    assert (set(box.functions), box.answer, box.max_rounds) == (
        {"lookup", "broken"},
        None,
        3,
    )
    assert [(c.tool, c.version) for c in box.code] == [(t, 1) for t in toolset.tools]


def test_a_tool_that_can_t_be_run_is_refused(plan: Plan) -> None:
    for bad, refused in (
        (tools.component("lookup", 2), "lookup is at version 1 in chatddx .*, not 2"),
        (tools.component("PARAMETERS"), "tools:PARAMETERS isn't shipped with chatddx"),
    ):
        made, _ = skeleton(plan, bad)
        with pytest.raises(LookupError, match=refused):
            _ = load(made, plan.registry.get)


def test_a_skeleton_without_tools_has_no_toolbox(plan: Plan) -> None:
    named = plan.named("recipe", LINES)
    assert (
        load(resolve(plan.registry.get, named.digest, Skeleton), plan.registry.get)
        is None
    )
