import pytest

from chatddx.bench import Bench
from chatddx.conftest import chosen
from chatddx.inventory import Inventory
from chatddx.repl.commands import handle
from chatddx.repl.shell import Repl, console
from chatddx.repl.test.helpers import Say
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import world_facts


@pytest.fixture
def template(request: pytest.FixtureRequest) -> str:
    return chosen(request, "curated")


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def bench(conn: Connection, world: Inventory) -> Bench:
    alice = People(conn).find("alice")
    assert alice is not None
    return Bench(conn, alice, world, world_facts())


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
