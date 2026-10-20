from collections.abc import Iterator

import pytest

from chatddx.curation import Plan
from chatddx.inventory import Inventory
from chatddx.runner.test.helpers import DELAY
from chatddx.test.helpers import added_alice, autocommitted
from chatddx.test.world import faked, free_world

__all__ = ["added_alice", "autocommitted"]


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
