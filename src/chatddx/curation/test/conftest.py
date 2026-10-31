from collections.abc import Iterator

import pytest

from chatddx.curation.test.cases import CASES, vignettes
from chatddx.store import People
from chatddx.test.helpers import Copies, connect, found_alice, templated
from chatddx.test.world import loaded as synced, world_plan

__all__ = ["found_alice"]


@pytest.fixture(scope="session")
def loaded(copies: Copies, migrated: str) -> Iterator[str]:
    with templated(copies, migrated) as name:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            _ = synced(conn, world_plan(), CASES, vignettes(), alice)
        yield name
