import pytest

from chatddx.bench import Bench
from chatddx.conftest import chosen
from chatddx.inventory import Inventory
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
