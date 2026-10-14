from collections.abc import Iterator

import pytest

from chatddx.conftest import Copies, connect, templated
from chatddx.curation import init
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.identity import Person
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import world_plan


# Alice and the archive after one init-data, without a giftbag, of the stand-in source.
@pytest.fixture(scope="session")
def loaded(copies: Copies, migrated: str) -> Iterator[str]:
    with templated(copies, migrated) as name:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            _ = init(conn, world_plan(), CASES, vignettes(), alice)
        yield name


# A test parametrized indirectly with a template's name, as "loaded", starts from it.
@pytest.fixture
def template(request: pytest.FixtureRequest) -> str:
    return request.getfixturevalue(getattr(request, "param", "migrated"))


@pytest.fixture
def alice(conn: Connection) -> Person:
    found = People(conn).find("alice")
    assert found is not None
    return found
