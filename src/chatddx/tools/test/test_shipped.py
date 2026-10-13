import importlib

import pytest

from chatddx.tools.shipped import TOOLS
from chatddx.tools.web_search import web_search

pytestmark = pytest.mark.solidified


def test_each_shipped_entry_point_names_the_function_it_ships() -> None:
    for entry_point, shipped in TOOLS.items():
        module, _, attribute = entry_point.partition(":")
        assert getattr(importlib.import_module(module), attribute) is shipped.function
    assert TOOLS["chatddx.tools.web_search:web_search"].function is web_search
