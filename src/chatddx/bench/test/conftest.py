import pytest

from chatddx.bench import Bench
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import Person
from chatddx.inventory import World
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import TEST


@pytest.fixture
def template(curated: str) -> str:
    return curated


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
    loaded = World.load(TEST)
    return Bench(conn, alice, loaded.inventory, Facts.load(BUNDLED, *loaded.facts))
