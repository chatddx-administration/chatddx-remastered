import json

import pytest
from pydantic import ValidationError

from chatddx.factors.base import StructuralError
from chatddx.factors.bundle import Registry
from chatddx.ledger import Turn
from chatddx.ledger.test.rounds import Rounds, ran, rounds

pytestmark = pytest.mark.wip


@pytest.fixture
def made() -> Rounds:
    return rounds(Registry())


def test_a_round_stopped_before_its_call_is_kept_and_noted(made: Rounds) -> None:
    two = made.call("web_search", "web_search")
    for tools, message in (
        (ran("c0"), "round 1 stopped after 1 of 2 tool calls, before its call"),
        (ran("c0", "c1"), "round 1 stopped after 2 of 2 tool calls, before its call"),
    ):
        unsent = Turn(tools=tools)
        assert made.item(two, unsent).calls == (two,)
        assert [(f.code, f.message) for f in made.findings(two, unsent)] == [
            ("tools.stopped", message)
        ]
    later = (
        Turn(tools=ran("c0", "c1"), call=two),
        Turn(tools=ran("c0", error="stopped")),
    )
    assert [f.message for f in made.findings(two, *later)] == [
        "round 2 stopped after 1 of 2 tool calls, before its call"
    ]


def test_a_round_without_its_call_leaves_no_call_in_the_record(made: Rounds) -> None:
    sent = made.item(made.call("web_search"), Turn(tools=ran("c0"), call=made.call()))
    unsent = made.item(made.call("web_search"), Turn(tools=ran("c0")))
    assert set(json.loads(sent.canonical)["turns"][0]) == {"tools", "call"}
    assert set(json.loads(unsent.canonical)["turns"][0]) == {"tools"}


def test_only_the_last_round_may_lack_its_call(made: Rounds) -> None:
    two = made.call("web_search", "web_search")
    with pytest.raises(ValidationError, match="only the last round may lack its call"):
        _ = made.item(two, Turn(tools=ran("c0")), Turn(tools=ran("c0"), call=two))


def test_a_round_without_its_call_runs_only_tools_the_response_called(
    made: Rounds,
) -> None:
    with pytest.raises(StructuralError, match="didn't make"):
        _ = made.check(made.call("web_search"), Turn(tools=ran("c0", "c1")))
