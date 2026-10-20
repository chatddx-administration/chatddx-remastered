import json
from typing import Any

from chatddx.fake_vllm.test.helpers import body, qwen, reply


def test_a_schema_s_examples_are_picked_by_the_seed_unless_greedy() -> None:
    verdict = {
        "type": "object",
        "properties": {"meets": {"type": "boolean", "examples": [True, False]}},
    }
    held = {"type": "json_schema", "json_schema": {"schema": verdict}}

    def meets(**fields: Any) -> bool:
        return json.loads(reply(qwen(), body(response_format=held, **fields)).content)[
            "meets"
        ]

    assert [meets(temperature=0.7, seed=s) for s in range(4)] == [True, False] * 2
    assert {meets(temperature=0, seed=s) for s in range(4)} == {True}
