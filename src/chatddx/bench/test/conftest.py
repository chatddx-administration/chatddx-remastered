from collections.abc import Iterator

import pytest

from chatddx.bench import Bench
from chatddx.conftest import SAMPLE_QWEN, WORLD, faked, free_world, sample_plan
from chatddx.curation import Plan
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People, Store
from chatddx.store.store import Connection


@pytest.fixture
def template(curated_sample: str) -> str:
    return curated_sample


# Pinned to the sample until this package's tests move to the test World.
@pytest.fixture
def world() -> Inventory:
    return free_world(WORLD)


@pytest.fixture
def fake(world: Inventory, conn: Connection) -> Iterator[None]:
    with faked(world, Store(conn).get, SAMPLE_QWEN):
        yield


@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


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
