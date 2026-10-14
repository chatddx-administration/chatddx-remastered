import pytest

from chatddx.bench import Bench
from chatddx.conftest import chosen
from chatddx.identity import Person
from chatddx.inventory import World
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import TEST, world_facts


@pytest.fixture
def template(request: pytest.FixtureRequest) -> str:
    return chosen(request, "curated")


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def alice(conn: Connection) -> Person:
    found = People(conn).find("alice")
    assert found is not None
    return found


@pytest.fixture
def bob(conn: Connection) -> Person:
    return People(conn).add("bob", "Bob")


@pytest.fixture
def bench(conn: Connection, alice: Person) -> Bench:
    inventory = World.load(TEST).inventory
    return Bench(conn, alice, inventory, world_facts())
