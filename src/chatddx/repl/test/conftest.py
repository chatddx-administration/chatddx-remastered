import pytest

from chatddx.bench import Bench
from chatddx.repl.commands import handle
from chatddx.repl.shell import Repl, console
from chatddx.repl.test.helpers import Say
from chatddx.test.helpers import autocommitted, curated_template, found_alices_bench

__all__ = ["autocommitted", "curated_template", "found_alices_bench"]


@pytest.fixture
def repl(bench: Bench) -> Repl:
    return Repl(bench, console(record=True, width=200), seed=7)


@pytest.fixture
def say(repl: Repl) -> Say:
    def said(*lines: str) -> str:
        for line in lines:
            assert handle(repl, line)
        return repl.console.export_text()

    return said
