from collections.abc import Iterator
from pathlib import Path

import pytest
from rich.console import Console

from chatddx.bench import Bench
from chatddx.conftest import free_world
from chatddx.facts import BUNDLED, Facts
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.inventory import Inventory, start_up
from chatddx.repl.commands import handle
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import QWEN, Say
from chatddx.store import People
from chatddx.store.store import Connection


@pytest.fixture
def template(curated: str) -> str:
    return curated


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def world(tmp_path: Path) -> Inventory:
    return free_world(tmp_path)


# The fake vLLM serving the Qwen endpoint's engine, as its start-up says.
@pytest.fixture
def fake(world: Inventory, bench: Bench) -> Iterator[None]:
    startup = start_up(world, bench.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])]):
        yield


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
