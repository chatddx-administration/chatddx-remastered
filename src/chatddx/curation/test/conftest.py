from collections.abc import Iterator

import pytest

from chatddx.conftest import Copies, connect, templated
from chatddx.curation import init
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.identity import Person
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import world_plan


@pytest.fixture(scope="session")
def loaded(copies: Copies, migrated: str) -> Iterator[str]:
    with templated(copies, migrated) as name:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            _ = init(conn, world_plan(), CASES, vignettes(), alice)
        yield name


@pytest.fixture
def alice(conn: Connection) -> Person:
    found = People(conn).find("alice")
    assert found is not None
    return found
