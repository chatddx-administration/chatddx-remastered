import json

import pytest
from pydantic import JsonValue

from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.fake_vllm.chat import instance
from chatddx.scorers.answer import Answer, read
from chatddx.test.world import LINES, NATIVE, TOOL_ANSWER


def skeleton(plan: Plan, recipe: str) -> Skeleton:
    return resolve(plan.registry.get, plan.named("recipe", recipe).digest, Skeleton)


def said(content: str | None = None, **message: JsonValue) -> dict[str, JsonValue]:
    said: dict[str, JsonValue] = {"role": "assistant", "content": content, **message}
    return {"choices": [{"index": 0, "message": said}]}


def called(name: str, arguments: str) -> dict[str, JsonValue]:
    function: JsonValue = {"name": name, "arguments": arguments}
    return said(tool_calls=[{"id": "call-1", "type": "function", "function": function}])


def test_a_native_answer_is_the_content_as_json(plan: Plan) -> None:
    made = skeleton(plan, NATIVE)
    document = instance(made.output_schema)
    assert read(made, said(json.dumps(document))) == Answer(document)
    assert read(made, said("{x")).problem is not None
    assert read(made, said("{x")).value is None
    assert read(made, said(None)) == Answer(None, "no content")
    assert read(made, said("null")) == Answer(None, "the content is null")


def test_an_answer_that_breaks_the_schema_is_kept_with_where_it_breaks(
    plan: Plan,
) -> None:
    made = skeleton(plan, NATIVE)
    broken: JsonValue = {
        "diagnoses": "sepsis",
        "acute_warning": None,
        "disposition": "",
    }
    found = read(made, said(json.dumps(broken)))
    assert found.value == broken
    assert found.problem == "at /diagnoses: 'sepsis' is not of type 'array'"


def test_a_tool_answer_is_the_answer_tool_s_arguments(plan: Plan) -> None:
    made = skeleton(plan, TOOL_ANSWER)
    document = instance(made.output_schema)
    assert read(made, called("final_result", json.dumps(document))) == Answer(document)
    assert read(made, called("lookup", "{}")) == Answer(
        None, "no call to the answer tool 'final_result'"
    )
    unread = read(made, called("final_result", "{x"))
    assert unread.value is None and unread.problem is not None
    assert unread.problem.startswith("the answer tool's arguments isn't JSON")


def test_a_text_answer_is_the_content(plan: Plan) -> None:
    made = skeleton(plan, LINES)
    assert read(made, said("Sepsis\nPneumonia")) == Answer("Sepsis\nPneumonia")
    assert read(made, said("  \n")) == Answer(None, "no content")


def test_a_text_answer_with_a_schema_is_the_json_in_it(plan: Plan) -> None:
    made = skeleton(plan, "prompted")
    document = instance(made.output_schema)
    text = json.dumps(document)
    assert read(made, said(text)) == Answer(document)
    fenced = f"Here is the plan.\n```json\n{text}\n```\nGood luck."
    assert read(made, said(fenced)) == Answer(document)
    thought = f'I considered {{"diagnoses": []}} first. Final answer: {text}'
    assert read(made, said(thought)) == Answer(document)
    assert read(made, said("no plan today")) == Answer(None, "no JSON in the content")


def test_no_response_is_no_answer(plan: Plan) -> None:
    assert read(skeleton(plan, NATIVE), None) == Answer(None, "no response")


CUT: list[tuple[str, JsonValue]] = [
    ('{"diagnoses": ["COPD", "PE"]\n\n\n', {"diagnoses": ["COPD", "PE"]}),
    ('{"diagnoses": ["Gastr', {"diagnoses": ["Gastr"]}),
    ('{"a": 1, "b": ', {"a": 1}),
    ('{"a": 1, "b', {"a": 1}),
    ('{"a": [1, 2, {"c": tr', {"a": [1, 2, {}]}),
    ('{"a": "x\\u00', {"a": "x"}),
    ('{"a": 1.', {"a": 1}),
    ("{", {}),
]


@pytest.mark.parametrize(("cut", "closed"), CUT)
def test_a_structured_answer_cut_short_is_read_with_its_structure_closed(
    plan: Plan, cut: str, closed: JsonValue
) -> None:
    found = read(skeleton(plan, NATIVE), said(cut))
    assert (found.value, found.salvaged) == (closed, True)
    assert read(skeleton(plan, TOOL_ANSWER), called("final_result", cut)).salvaged


@pytest.mark.parametrize("broken", ['{"a": 1} more', '{"a": x', '{"a": 1]', "nothing"])
def test_json_that_breaks_before_its_end_isn_t_salvaged(
    plan: Plan, broken: str
) -> None:
    found = read(skeleton(plan, NATIVE), said(broken))
    assert (found.value, found.salvaged) == (None, False)
    assert found.problem is not None and "isn't JSON" in found.problem


def test_a_text_answer_cut_short_isn_t_salvaged(plan: Plan) -> None:
    found = read(skeleton(plan, "prompted"), said('{"diagnoses": ["Sepsis"'))
    assert (found.value, found.salvaged) == (None, False)
