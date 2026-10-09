from collections.abc import Iterator

import psycopg
import pytest

from chatddx.bench import Bench
from chatddx.conftest import WORLD, create_database, drop_database, sample_plan
from chatddx.core import settings
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.seed import Plan
from chatddx.store import People
from chatddx.store.store import Connection


@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


@pytest.fixture
def db(seeded: str) -> Iterator[str]:
    name = create_database(template=seeded)
    try:
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def conn(db: str) -> Iterator[Connection]:
    with psycopg.connect(settings.database(), dbname=db, autocommit=True) as c:
        yield c


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
    return Bench(conn, alice, Inventory.load(WORLD), Facts.load(BUNDLED))
