import pytest
from pydantic import JsonValue

from chatddx.factors.request import Tool
from chatddx.tools.shipped import TOOLS, ShippedTool

PARAMETERS: dict[str, JsonValue] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "max_results": {"type": "integer", "default": 5},
    },
    "required": ["query"],
    "additionalProperties": False,
}


def lookup(query: str, max_results: int = 5) -> str:
    return f"{max_results} results for {query!r}"


def broken(query: str, **_: object) -> str:
    raise OSError(f"no answer for {query!r}")


def counted(query: str, max_results: int = 5) -> int:
    return len(query) + max_results


def component(function: str, version: int = 1) -> Tool:
    return Tool(
        name=function,
        description=f"{function}, for the runner's tests",
        parameters=PARAMETERS,
        entry_point=f"chatddx.runner.test.tools:{function}",
        version=version,
    )


def shipped(monkeypatch: pytest.MonkeyPatch) -> None:
    for function in (lookup, broken, counted):
        entry_point = f"chatddx.runner.test.tools:{function.__name__}"
        monkeypatch.setitem(TOOLS, entry_point, ShippedTool(1, function))
