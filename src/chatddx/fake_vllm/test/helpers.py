from typing import Any

from chatddx.fake_vllm.chat import (
    Reply,
    accept,
    respond,
)
from chatddx.fake_vllm.served import Served
from chatddx.test.world import QWEN_MODEL

TOOLS = ("--enable-auto-tool-choice", "--tool-call-parser")
# As the old chatddx served them (chatddx 7893656, src/chatddx/data/inventory/malborg.toml).
QWEN_ARGV = ("--reasoning-parser", "qwen3", *TOOLS[:1], TOOLS[1], "hermes")
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}


def body(model: str = QWEN_MODEL, **fields: Any) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [{"role": "user", "content": "a cough"}],
    } | fields


def qwen(*argv: str) -> Served:
    return Served.of(QWEN_MODEL, argv or QWEN_ARGV)


def reply(served: Served, request: dict[str, Any], runaway: bool = False) -> Reply:
    return respond(accept([served], request), request, runaway)


def function(name: str, parameters: Any = None) -> dict[str, Any]:
    return {"type": "function", "function": {"name": name, "parameters": parameters}}
