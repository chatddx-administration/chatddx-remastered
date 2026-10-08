from pydantic import JsonValue

from chatddx.core.rig import rig
from chatddx.factors.base import Code
from chatddx.factors.request import Tool

# Tools for the runner's tests, which mustn't reach a third party as
# `chatddx.tools.web_search` does. They take its parameters.
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


NOT_A_FUNCTION = "lookup"


def component(function: str, code: Code | None = None) -> Tool:
    return Tool(
        name=function,
        description=f"{function}, for the runner's tests",
        parameters=PARAMETERS,
        code=code or rig(),
        entry_point=f"chatddx.runner.test.tools:{function}",
    )
