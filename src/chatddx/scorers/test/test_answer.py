import json

import pytest
from pydantic import JsonValue

from chatddx.conftest import sample_plan
from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.fake_vllm.chat import instance
from chatddx.scorers.answer import Answer, read


@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


def skeleton(plan: Plan, recipe: str) -> Skeleton:
    named = plan.named("recipe", f"{recipe} (en, Qwen/Qwen3-8B-AWQ)")
    return resolve(plan.registry.get, named.digest, Skeleton)


def said(content: str | None = None, **message: JsonValue) -> dict[str, JsonValue]:
    said: dict[str, JsonValue] = {"role": "assistant", "content": content, **message}
    return {"choices": [{"index": 0, "message": said}]}


def called(name: str, arguments: str) -> dict[str, JsonValue]:
    function: JsonValue = {"name": name, "arguments": arguments}
    return said(tool_calls=[{"id": "call-1", "type": "function", "function": function}])


def test_a_native_answer_is_the_content_as_json(plan: Plan) -> None:
    made = skeleton(plan, "plan")
    document = instance(made.output_schema)
    assert read(made, said(json.dumps(document))) == Answer(document)
    assert read(made, said("{")).problem is not None
    assert read(made, said("{")).value is None
    assert read(made, said(None)) == Answer(None, "no content")
    assert read(made, said("null")) == Answer(None, "the content is null")


def test_an_answer_that_breaks_the_schema_is_kept_with_where_it_breaks(
    plan: Plan,
) -> None:
    made = skeleton(plan, "diagnoses")
    broken: JsonValue = {"diagnoses": "sepsis"}
    found = read(made, said(json.dumps(broken)))
    assert found.value == broken
    assert found.problem == "at /diagnoses: 'sepsis' is not of type 'array'"


def test_a_tool_answer_is_the_answer_tool_s_arguments(plan: Plan) -> None:
    made = skeleton(plan, "diagnoses-tool")
    document = instance(made.output_schema)
    assert read(made, called("final_result", json.dumps(document))) == Answer(document)
    assert read(made, called("web_search", "{}")) == Answer(
        None, "no call to the answer tool 'final_result'"
    )
    unread = read(made, called("final_result", "{"))
    assert unread.value is None and unread.problem is not None
    assert unread.problem.startswith("the answer tool's arguments isn't JSON")


def test_a_text_answer_is_the_content(plan: Plan) -> None:
    made = skeleton(plan, "free-text")
    assert read(made, said("Sepsis\nPneumonia")) == Answer("Sepsis\nPneumonia")
    assert read(made, said("  \n")) == Answer(None, "no content")


def test_a_text_answer_with_a_schema_is_the_json_in_it(plan: Plan) -> None:
    made = skeleton(plan, "plan-prompted")
    document = instance(made.output_schema)
    text = json.dumps(document)
    assert read(made, said(text)) == Answer(document)
    fenced = f"Here is the plan.\n```json\n{text}\n```\nGood luck."
    assert read(made, said(fenced)) == Answer(document)
    thought = f'I considered {{"diagnoses": []}} first. Final answer: {text}'
    assert read(made, said(thought)) == Answer(document)
    assert read(made, said("no plan today")) == Answer(None, "no JSON in the content")


def test_no_response_is_no_answer(plan: Plan) -> None:
    assert read(skeleton(plan, "plan"), None) == Answer(None, "no response")
