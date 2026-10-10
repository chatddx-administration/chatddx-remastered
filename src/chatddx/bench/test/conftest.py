import pytest

from chatddx.bench import Bench
from chatddx.conftest import WORLD
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People
from chatddx.store.store import Connection


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
    return Bench(
        conn, alice, Inventory.load(WORLD / "inventory.toml"), Facts.load(BUNDLED)
    )
