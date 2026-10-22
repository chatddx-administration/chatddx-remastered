from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.identity import Person
from chatddx.inventory import World
from chatddx.portal.app import app
from chatddx.portal.test.helpers import signing_in
from chatddx.test.helpers import alice_with_password, autocommitted, curated_template
from chatddx.test.world import TEST

__all__ = ["alice_with_password", "autocommitted", "curated_template"]


# Policy: a browser test starts a browser, so it runs only when asked for by its mark.
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if "browser" in (config.getoption("markexpr") or ""):
        return
    skip = pytest.mark.skip(reason="it starts a browser: pytest -m browser")
    for item in items:
        if "browser" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def built(tmp_path: Path) -> Path:
    return tmp_path / "dist"


@pytest.fixture
def served(db: str, built: Path) -> FastAPI:
    return app(
        World.load(TEST),
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
