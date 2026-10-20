import pytest

from chatddx.bench import Bench
from chatddx.identity import Person
from chatddx.inventory import World
from chatddx.store.store import Connection
from chatddx.test.helpers import (
    added_bob,
    autocommitted,
    curated_template,
    found_alice,
)
from chatddx.test.world import TEST

__all__ = ["added_bob", "autocommitted", "curated_template", "found_alice"]


@pytest.fixture
def bench(conn: Connection, alice: Person) -> Bench:
    inventory = World.load(TEST).inventory
    return Bench(conn, alice, inventory)
