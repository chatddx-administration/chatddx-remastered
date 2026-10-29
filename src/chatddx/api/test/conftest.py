from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.api.app import app
from chatddx.api.test.helpers import bearer, listened
from chatddx.bench import Bench
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.helpers import (
    alice_with_password,
    autocommitted,
    curated_template,
)
from chatddx.test.world import TEST

__all__ = ["alice_with_password", "autocommitted", "curated_template"]


@pytest.fixture
def served(db: str) -> FastAPI:
    return app(
        Inventory.load(TEST / "inventory.toml"),
        make_conninfo(settings.database(), dbname=db),
        worker=True,
    )


@pytest.fixture
def listening(served: FastAPI) -> Iterator[str]:
    with listened(served) as (url, _):
        yield url


@pytest.fixture
def client(served: FastAPI) -> Iterator[TestClient]:
    with TestClient(served, base_url="https://testserver") as c:
        yield c


@pytest.fixture
def signed(client: TestClient, conn: Connection, alice: Person) -> TestClient:
    client.headers.update(bearer(conn, alice))
    return client


@pytest.fixture
def bob(conn: Connection) -> dict[str, str]:
    return bearer(conn, People(conn).add("bob", "Bob"))


@pytest.fixture
def bench(served: FastAPI, conn: Connection, alice: Person) -> Bench:
    held = served.state.chatddx
    return Bench(conn, alice, held.inventory)
