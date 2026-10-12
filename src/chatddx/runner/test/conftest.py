from collections.abc import Iterator

import pytest

from chatddx.curation import Plan
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import faked, free_world

from . import tools

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


@pytest.fixture
def inventory() -> Inventory:
    return free_world()


@pytest.fixture
def fake(inventory: Inventory, plan: Plan) -> Iterator[None]:
    with faked(inventory, plan.registry.get):
        yield


@pytest.fixture
def delayed(inventory: Inventory, plan: Plan) -> Iterator[None]:
    with faked(inventory, plan.registry.get, delay=DELAY):
        yield
