from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.app import app
from chatddx.portal.test.helpers import signing_in
from chatddx.test.helpers import alice_with_password, autocommitted, curated_template
from chatddx.test.world import TEST

__all__ = ["alice_with_password", "autocommitted", "curated_template"]


@pytest.fixture
def built(tmp_path: Path) -> Path:
    return tmp_path / "dist"


@pytest.fixture
def served(db: str, built: Path) -> FastAPI:
    return app(
        Inventory.load(TEST / "inventory.toml"),
        make_conninfo(settings.database(), dbname=db),
        built,
        worker=True,
    )


@pytest.fixture
def client(served: FastAPI) -> Iterator[TestClient]:
    with TestClient(served, base_url="https://testserver", follow_redirects=False) as c:
        yield c


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client
