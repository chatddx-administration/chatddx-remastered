from collections.abc import Callable
from dataclasses import dataclass

from .web_search import web_search


@dataclass(frozen=True)
class ShippedTool:
    version: int
    function: Callable[..., object]


TOOLS: dict[str, ShippedTool] = {
    "chatddx.tools.web_search:web_search": ShippedTool(1, web_search),
}
