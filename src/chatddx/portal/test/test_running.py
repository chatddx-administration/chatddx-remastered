import time
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.app import app
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, QWEN, faked, world_facts


@pytest.fixture
def served(db: str, built: Path, world: Inventory) -> FastAPI:
    return app(
        world,
        world_facts(),
        make_conninfo(settings.database(), dbname=db),
        built,
        worker=True,
    )


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def started(signed: TestClient, **more: Any) -> str:
    query = {"kind": "configuration", "name": LINES, "owner": "alice"}
    [lines] = signed.get("/api/threads", params=query).json()
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    body = {"configuration": lines["id"], "endpoint": QWEN, "families": [crlf["id"]]}
    got = signed.post("/api/runs", json={**body, **more})
    assert got.status_code == 202, got.json()
    return got.json()["run"]


def settled(signed: TestClient, run: str) -> dict[str, Any]:
    for _ in range(500):
        found = signed.get(f"/api/runs/{run}").json()
        if found["finished"] and "under way" not in shown(signed, f"/runs/{run}"):
            return found
        time.sleep(0.02)
    raise AssertionError(f"run {run} is still under way")


@pytest.mark.slow
def test_a_run_under_way_is_followed_and_halted_on_its_page(
    signed: TestClient, world: Inventory, conn: Connection
) -> None:
    with faked(world, Store(conn).get, delay=0.2):
        run = started(signed)
        page = shown(signed, f"/runs/{run}")
        assert "Something is under way for this run" in page
        assert 'id="run-live-props"' in page and f'"run": "{run}"' in page
        assert f'action="/runs/{run}/halt"' in page
        assert "Run again" not in page and "Items</h2>" not in page

        got = signed.post(f"/runs/{run}/halt")
        assert (got.status_code, got.headers["location"]) == (303, f"/runs/{run}")
        _ = settled(signed, run)

    page = shown(signed, f"/runs/{run}")
    assert "Items</h2>" in page and 'id="run-live"' not in page
    assert f'action="/runs/{run}/halt"' not in page
    assert f'action="/runs/{run}/scores"' in page and "Left to score by" in page
    assert f'action="/runs/{run}/again"' in page
    left = shown(signed, "/runs?left=true")
    assert f'action="/runs/{run}/scores"' in left

    got = signed.post(f"/runs/{run}/halt")
    assert got.status_code == 409 and "A conflict" in got.text


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_is_scored_again_and_run_again_from_its_page(signed: TestClient) -> None:
    run = started(signed, score=False)
    _ = settled(signed, run)
    assert "Left to score by" in shown(signed, f"/runs/{run}")

    got = signed.post(f"/runs/{run}/scores")
    assert (got.status_code, got.headers["location"]) == (303, f"/runs/{run}")
    scored = settled(signed, run)
    assert scored["scores"] and "Left to score by" not in shown(signed, f"/runs/{run}")

    got = signed.post(f"/runs/{run}/again")
    assert got.status_code == 303
    again = got.headers["location"].removeprefix("/runs/")
    assert again != run
    shown_again = settled(signed, again)
    assert (shown_again["skeleton"], shown_again["cases"]) == (
        scored["skeleton"],
        scored["cases"],
    )
    assert (
        shown_again["described"].split(" (seed")[0]
        == scored["described"].split(" (seed")[0]
    )


@pytest.mark.slow
def test_a_form_from_another_site_starts_nothing(signed: TestClient) -> None:
    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    for action in ("halt", "scores", "again"):
        got = signed.post(
            "/runs/00000000-0000-0000-0000-000000000000/" + action, headers=elsewhere
        )
        assert got.status_code == 403
