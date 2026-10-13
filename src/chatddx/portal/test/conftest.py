from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx.core import settings
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.app import app
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import TEST, world_facts

PASSWORD = "correct horse battery staple"


@pytest.fixture
def template(curated: str) -> str:
    return curated


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def alice(conn: Connection) -> Person:
    people = People(conn)
    found = people.find("alice")
    assert found is not None
    people.set_password(found.id, PASSWORD)
    return found


@pytest.fixture
def served(db: str) -> FastAPI:
    return app(
        Inventory.load(TEST / "inventory.toml"),
        world_facts(),
        make_conninfo(settings.database(), dbname=db),
    )


@pytest.fixture
def client(served: FastAPI) -> Iterator[TestClient]:
    with TestClient(served, base_url="https://testserver", follow_redirects=False) as c:
        yield c
