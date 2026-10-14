from pydantic import JsonValue

from chatddx.factors.response import (
    Part,
    ToolCall,
    choice,
    message,
    parts,
    reasoning,
    tool_calls,
)

CALL: dict[str, JsonValue] = {
    "id": "c1",
    "type": "function",
    "function": {"name": "web_search", "arguments": '{"query": "ACS"}'},
}


def answered(said: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return {"choices": [{"index": 0, "message": said, "token_ids": [1, 2]}]}


def test_the_first_choice_and_its_message_or_nothing() -> None:
    response = answered({"content": "ACS"})
    assert choice(response)["token_ids"] == [1, 2]
    assert message(response) == {"content": "ACS"}
    broken: list[dict[str, JsonValue]] = [
        {},
        {"choices": []},
        {"choices": ["ACS"]},
        {"choices": [{}]},
    ]
    for response in broken:
        assert message(response) == {}
    assert choice({"choices": "ACS"}) == {}


def test_reasoning_is_read_under_either_name_reasoning_first() -> None:
    assert reasoning({"reasoning": "Hm.", "reasoning_content": "Other."}) == "Hm."
    assert reasoning({"reasoning": "", "reasoning_content": "Hm."}) == "Hm."
    assert reasoning({"reasoning_content": "Hm."}) == "Hm."
    assert reasoning({"reasoning": None, "content": "ACS"}) is None


def test_a_tool_call_needs_an_id_a_name_and_arguments() -> None:
    nameless: JsonValue = {"id": "c2", "function": {"arguments": "{}"}}
    unnumbered: JsonValue = {"function": {"name": "web_search", "arguments": "{}"}}
    response = answered({"tool_calls": [CALL, nameless, unnumbered]})
    assert tool_calls(response) == (
        ToolCall(id="c1", name="web_search", arguments='{"query": "ACS"}'),
    )


def test_a_message_s_parts_in_the_order_it_was_thought_written_and_called() -> None:
    said: dict[str, JsonValue] = {
        "reasoning_content": "Let me check.",
        "content": "ACS",
        "tool_calls": [CALL],
    }
    assert parts(answered(said)) == [
        Part("reasoning", "Let me check."),
        Part("content", "ACS"),
        Part("tool_call", '{"query": "ACS"}', "web_search"),
    ]
    assert parts(answered({"content": "", "reasoning": ""})) == []
