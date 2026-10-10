from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from chatddx.conftest import free_world
from chatddx.curation import Plan
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.identity import Person
from chatddx.inventory import Inventory, start_up
from chatddx.store import People
from chatddx.store.store import Connection

QWEN = "qwen3-8b-awq@fake"
# Slow enough that calls sent together overlap: a fake answer is some 40 tokens.
DELAY = 0.005


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def alice(conn: Connection) -> Person:
    return People(conn).add("alice", "Alice")


@pytest.fixture
def inventory(tmp_path: Path) -> Inventory:
    return free_world(tmp_path)


@contextmanager
def faked(inventory: Inventory, plan: Plan, delay: float = 0.0) -> Generator[None]:
    startup = start_up(inventory, plan.registry.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])], delay=delay):
        yield


@pytest.fixture
def fake(inventory: Inventory, plan: Plan) -> Iterator[None]:
    with faked(inventory, plan):
        yield


@pytest.fixture
def delayed(inventory: Inventory, plan: Plan) -> Iterator[None]:
    with faked(inventory, plan, DELAY):
        yield
