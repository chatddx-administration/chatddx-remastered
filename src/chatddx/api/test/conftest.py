from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from psycopg.conninfo import make_conninfo

from chatddx.api.app import app
from chatddx.bench import Bench
from chatddx.conftest import SAMPLE_QWEN, WORLD, faked, free_world
from chatddx.core import settings
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People, Store
from chatddx.store.store import Connection

PASSWORD = "correct horse battery staple"


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
        Inventory.load(WORLD / "inventory.toml"),
        Facts.load(BUNDLED),
        make_conninfo(settings.database(), dbname=db),
    )


@pytest.fixture
def client(served: FastAPI) -> Iterator[TestClient]:
    with TestClient(served, base_url="https://testserver") as c:
        yield c


def sign_in(
    client: TestClient, login: str = "alice", password: str = PASSWORD, **headers: str
) -> Response:
    body = {"login": login, "password": password}
    return client.post("/api/session", json=body, headers=headers)


def bearer(conn: Connection, person: Person) -> dict[str, str]:
    return {"Authorization": f"Bearer {People(conn).open_session(person.id)}"}


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
    return Bench(conn, alice, held.inventory, held.facts)
