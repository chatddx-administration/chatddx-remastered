from collections.abc import Generator, Iterator
from contextlib import contextmanager

import pytest

from chatddx.conftest import WORLD, free_world, sample_plan
from chatddx.curation import Plan
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.identity import Person
from chatddx.inventory import Inventory, start_up
from chatddx.store import People
from chatddx.store.store import Connection

from . import tools

QWEN = "qwen3-8b-awq@fake"
# Slow enough that calls sent together overlap: a fake answer is some 40 tokens.
DELAY = 0.005


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture(autouse=True)
def shipped_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    tools.shipped(monkeypatch)


@pytest.fixture
def alice(conn: Connection) -> Person:
    return People(conn).add("alice", "Alice")


# Pinned to the sample until this package's tests move to the test World.
@pytest.fixture
def inventory() -> Inventory:
    return free_world(WORLD)


@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


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
