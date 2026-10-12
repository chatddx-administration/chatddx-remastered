from collections.abc import Iterator

import pytest
from rich.console import Console

from chatddx.bench import Bench
from chatddx.conftest import SAMPLE_QWEN, WORLD, faked, free_world
from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import Inventory
from chatddx.repl.commands import handle
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import Say
from chatddx.store import People, Store
from chatddx.store.store import Connection


@pytest.fixture
def template(curated_sample: str) -> str:
    return curated_sample


# Pinned to the sample until this package's tests move to the test World.
@pytest.fixture
def world() -> Inventory:
    return free_world(WORLD)


@pytest.fixture
def fake(world: Inventory, conn: Connection) -> Iterator[None]:
    with faked(world, Store(conn).get, SAMPLE_QWEN):
        yield


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def bench(conn: Connection, world: Inventory) -> Bench:
    alice = People(conn).find("alice")
    assert alice is not None
    return Bench(conn, alice, world, Facts.load(BUNDLED))


@pytest.fixture
def repl(bench: Bench) -> Repl:
    return Repl(bench, Console(record=True, width=200), seed=7)


@pytest.fixture
def say(repl: Repl) -> Say:
    def said(*lines: str) -> str:
        for line in lines:
            assert handle(repl, line)
        return repl.console.export_text()

    return said
