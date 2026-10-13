from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx.api.app import app
from chatddx.api.test.test_runs import asked, family
from chatddx.bench import Bench
from chatddx.bench.test.helpers import ran, trial
from chatddx.core import settings
from chatddx.curation import Plan
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store.store import Connection
from chatddx.test.world import LINES, world_facts

pytestmark = pytest.mark.wip


@pytest.fixture
def served(db: str, world: Inventory) -> FastAPI:
    return app(world, world_facts(), make_conninfo(settings.database(), dbname=db))


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_s_scores_are_read_with_their_items_and_judge_calls(
    signed: TestClient, bench: Bench, bob: dict[str, str]
) -> None:
    noted = family(signed, "noted")["id"]
    made = signed.post("/api/runs", json=asked(signed, families=[noted])).json()
    run = made["id"]
    latest = signed.get(f"/api/runs/{run}/scores").json()
    assert latest == made["scores"]
    judged = next(g for g in latest if g["name"] == "judged")
    assert judged["finished"] and judged["scoring"] and judged["at"]
    path = f"/api/runs/{run}/scores/{judged['score']}"
    assert signed.get(path).json() == judged

    shown = signed.get(f"{path}/items").json()
    views = {i["view"]: i for i in shown["items"]}
    assert sorted(views) == [0, 1, 2, 3]
    assert views[0]["judge_calls"] == []
    assert [len(views[v]["judge_calls"]) for v in (1, 2, 3)] == [1, 1, 3]
    assert views[3]["detail"] is not None
    assert shown["findings"] == []

    _ = bench.score(bench.run_by_id(UUID(run)))
    every = signed.get(f"/api/runs/{run}/scores", params={"all": "true"}).json()
    again = signed.get(f"/api/runs/{run}/scores").json()
    assert len(every) == 2 * len(latest)
    assert {g["score"] for g in every[: len(latest)]} == {g["score"] for g in again}
    assert signed.get(path).json() == judged

    assert signed.get(f"/api/runs/{run}/scores", headers=bob).status_code == 404
    assert signed.get(f"{path}/items", headers=bob).status_code == 404
    assert signed.get(f"/api/runs/{run}/scores/{uuid4()}").status_code == 404


@pytest.mark.slow
def test_the_runs_left_to_score_are_listed_with_their_scorers(
    signed: TestClient, conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    left = ran(conn, alice, trial(conn, plan, LINES, "crlf"))
    _ = ran(conn, alice, trial(conn, plan, LINES, "crlf"), finished=False)

    [listed] = signed.get("/api/runs", params={"unscored": "true"}).json()
    assert listed["id"] == str(left)
    assert {s["name"] for s in listed["unscored"]} == {"lines", "whole", "judged"}
    assert all(r["unscored"] is None for r in signed.get("/api/runs").json())

    lines = plan.named("scorer", "lines").digest
    _ = bench.score(bench.run_by_id(left), {lines})
    [after] = signed.get("/api/runs", params={"unscored": "true"}).json()
    assert {s["name"] for s in after["unscored"]} == {"whole", "judged"}


def test_scores_need_a_session(client: TestClient) -> None:
    run, score = uuid4(), uuid4()
    for path in (
        f"/api/runs/{run}/scores",
        f"/api/runs/{run}/scores/{score}",
        f"/api/runs/{run}/scores/{score}/items",
    ):
        assert client.get(path).status_code == 401
