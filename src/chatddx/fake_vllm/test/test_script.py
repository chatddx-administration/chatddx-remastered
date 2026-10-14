import json
import tomllib
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from chatddx.fake_vllm.script import Script
from chatddx.fake_vllm.served import Refused, Served
from chatddx.fake_vllm.server import serving

QWEN = "Qwen/Qwen3-8B-AWQ"
PARSED = [
    *("--reasoning-parser", "qwen3"),
    *("--enable-auto-tool-choice", "--tool-call-parser", "hermes"),
]
SCRIPT = """
[[turn]]
reasoning = "Upper abdominal pain after a fatty meal."
content = "Biliary colic"

[[turn]]
tool_calls = [{ name = "final_result", arguments = { diagnoses = ["Biliary colic"] } }]

[[turn]]
status = 503
content = "the engine is loading"

[[turn]]
content = "Cholecystitis"
hang_up = 1

[[turn]]
content = "Pancreatitis"
runaway = 3
"""


def body(**fields: Any) -> bytes:
    message = {"role": "user", "content": "a case"}
    return json.dumps(
        {"model": QWEN, "messages": [message], "stream": True} | fields
    ).encode()


def post(url: str, data: bytes) -> tuple[int, list[dict[str, Any]], bool]:
    request = urllib.request.Request(f"{url}/v1/chat/completions", data=data)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, [json.loads(e.read())], False
    events = [e.removeprefix("data: ") for e in raw.split("\n\n") if e]
    done = events[-1:] == ["[DONE]"]
    return 200, [json.loads(e) for e in events if e != "[DONE]"], done


def said(chunks: list[dict[str, Any]], field: str) -> str:
    return "".join(
        str(c["choices"][0]["delta"].get(field) or "") for c in chunks if c["choices"]
    )


def calls(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for c in chunks:
        if not c["choices"]:
            continue
        deltas: list[dict[str, Any]] = c["choices"][0]["delta"].get("tool_calls") or []
        found += [d.get("function") or {} for d in deltas]
    return found


def finish(chunks: list[dict[str, Any]]) -> str | None:
    found = [c["choices"][0].get("finish_reason") for c in chunks if c["choices"]]
    return next((f for f in reversed(found) if f), None)


@pytest.fixture
def url() -> Iterator[str]:
    served = Served.of(QWEN, PARSED)
    with serving([served], "127.0.0.1", 0, script=Script.of(_parsed())) as (h, p):
        yield f"http://{h}:{p}"


def _parsed() -> dict[str, Any]:
    return tomllib.loads(SCRIPT)


def test_each_request_is_answered_with_the_script_s_next_turn(url: str) -> None:
    status, chunks, done = post(url, body())
    assert (status, done) == (200, True)
    assert said(chunks, "reasoning") == "Upper abdominal pain after a fatty meal."
    assert said(chunks, "content") == "Biliary colic"
    assert finish(chunks) == "stop"

    status, chunks, done = post(url, body())
    [call] = [c for c in calls(chunks) if c.get("name")]
    assert call["name"] == "final_result"
    assert finish(chunks) == "tool_calls"

    status, [error], _ = post(url, body())
    assert status == 503
    assert error["error"]["message"] == "the engine is loading"

    status, chunks, done = post(url, body())
    assert (status, done) == (200, False)
    assert said(chunks, "content") == "Cholecystitis"

    status, chunks, done = post(url, body())
    assert said(chunks, "content") == "Pancreatitis\n\n\n"
    assert finish(chunks) == "length"

    status, [error], _ = post(url, body())
    assert status == 500
    assert error["error"]["message"] == "the script has no turn left for this request"


def test_a_scripted_thought_goes_where_the_server_puts_reasoning() -> None:
    script = Script.of(_parsed())
    with serving([Served.of(QWEN)], "127.0.0.1", 0, script=script) as (h, p):
        _, chunks, _ = post(f"http://{h}:{p}", body())

    assert said(chunks, "reasoning") == ""
    assert said(chunks, "content") == (
        "<think>\nUpper abdominal pain after a fatty meal.\n</think>\n\nBiliary colic"
    )


def test_a_scripted_request_still_meets_vllm_s_checks() -> None:
    script = Script.of(_parsed())
    with serving([Served.of(QWEN)], "127.0.0.1", 0, script=script) as (h, p):
        status, [error], _ = post(f"http://{h}:{p}", body(tool_choice="required"))

    assert status == 400 and error["error"]["param"] == "tool_choice"
    assert script.next() == (1, script.turns[0])


@pytest.mark.parametrize(
    ("text", "refusal"),
    [
        ("", "has no \\[\\[turn\\]\\]"),
        ("[[turn]]\nwords = 'x'\n", r"turn 1 has no \['words'\]"),
        ("[[turn]]\ncontent = 1\n", "turn 1.content is text"),
        ("[[turn]]\nhang_up = -1\n", "turn 1.hang_up is a count"),
        ("[[turn]]\ntool_calls = [{ name = 'x', id = 'y' }]\n", r"has no \['id'\]"),
    ],
)
def test_a_script_says_what_it_can_t_read(
    tmp_path: Path, text: str, refusal: str
) -> None:
    path = tmp_path / "script.toml"
    _ = path.write_text(text)
    with pytest.raises(Refused, match=refusal):
        _ = Script.load(path)
