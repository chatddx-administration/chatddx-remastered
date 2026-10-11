from collections.abc import Callable
from dataclasses import dataclass

from .web_search import web_search


# A tool's function, at the version its developers raise when what it does changes.
@dataclass(frozen=True)
class ShippedTool:
    version: int
    function: Callable[..., object]


# The tool code chatddx ships, by the entry point a tool pins.
TOOLS: dict[str, ShippedTool] = {
    "chatddx.tools.web_search:web_search": ShippedTool(1, web_search),
}
