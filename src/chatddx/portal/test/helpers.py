import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.inventory import Inventory
from chatddx.portal.app import app
from chatddx.test.helpers import PASSWORD


def signing_in(
    client: TestClient, password: str = PASSWORD, next: str = "/", **headers: str
) -> Response:
    form = {"login": "alice", "password": password, "next": next}
    return client.post("/sign-in", data=form, headers=headers)


def shown(client: TestClient, path: str) -> str:
    got = client.get(path)
    assert got.status_code == 200, (path, got.text[:500])
    assert got.headers["content-type"].startswith("text/html")
    assert got.headers["cache-control"] == "no-store"
    return got.text


def variation_props(page: str) -> dict[str, Any]:
    opened = '<script type="application/json" id="variation-props">'
    return json.loads(page.split(opened, 1)[1].split("</script>", 1)[0])


def thread_props(page: str) -> dict[str, Any]:
    return variation_props(page.replace('id="thread-props"', 'id="variation-props"'))


# Accommodating for pytest, as src/chatddx/test/helpers.py:curated_template does.
@pytest.fixture(name="template")
def ran_template(ran: str) -> str:
    return ran


@pytest.fixture(name="served")
def world_served(db: str, built: Path, world: Inventory) -> FastAPI:
    return app(
        world,
        make_conninfo(settings.database(), dbname=db),
        built,
        worker=True,
    )
