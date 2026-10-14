from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx.api.app import app
from chatddx.api.test.test_runs import asked, family, followed, names, sent
from chatddx.bench import Bench
from chatddx.bench.test.helpers import ran, trial
from chatddx.core import settings
from chatddx.curation import Plan
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, faked, world_facts


@pytest.fixture
def served(db: str, world: Inventory) -> FastAPI:
    return app(world, world_facts(), make_conninfo(settings.database(), dbname=db))


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_s_scores_are_read_with_their_items_and_judge_calls(
    signed: TestClient, bob: dict[str, str]
) -> None:
    noted = family(signed, "noted")["id"]
    made, _ = sent(signed, asked(signed, families=[noted]))
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

    got = signed.post(f"/api/runs/{run}/scores", json={})
    assert got.status_code == 202
    assert got.headers["location"] == f"/api/runs/{run}/scores"
    assert {s["name"] for s in got.json()["scorers"]} == {g["name"] for g in latest}
    said = followed(signed, run)
    assert names(said)[0] == "run.scoring" and names(said)[-2:] == [
        "run.scored",
        "done",
    ]
    assert {"score.started", "score.item", "judge.asked", "judge.answered"} <= set(
        names(said)
    )
    asked_ = [d for _, n, d in said if n == "judge.asked"]
    assert len(asked_) == 5 and {d["view"] for d in asked_} == {1, 2, 3}
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


@pytest.mark.slow
def test_a_run_is_scored_when_asked_and_what_can_t_be_is_refused(
    signed: TestClient,
    conn: Connection,
    alice: Person,
    plan: Plan,
    world: Inventory,
    bob: dict[str, str],
) -> None:
    unfinished = ran(conn, alice, trial(conn, plan, LINES, "crlf"), finished=False)
    left = ran(conn, alice, trial(conn, plan, LINES, "crlf"))
    lines = plan.named("scorer", "lines").digest
    other = plan.named("scorer", "answer").digest
    for run, body, status, said in (
        (unfinished, {}, 422, f"run {unfinished} hasn't finished"),
        (
            left,
            {"scorers": [other]},
            422,
            f"scorer {other} doesn't apply to run {left}",
        ),
        (uuid4(), {}, 404, "of yours"),
    ):
        got = signed.post(f"/api/runs/{run}/scores", json=body)
        assert got.status_code == status and said in got.json()["detail"]
    assert (
        signed.post(f"/api/runs/{left}/scores", json={}, headers=bob).status_code == 404
    )

    got = signed.post(f"/api/runs/{left}/scores", json={"scorers": [lines]})
    assert [s["name"] for s in got.json()["scorers"]] == ["lines"]
    said = followed(signed, str(left))
    [scored] = [d for _, n, d in said if n == "run.scored"]
    assert [g["name"] for g in scored["scores"]] == ["lines"]

    noted = asked(signed, families=[family(signed, "noted")["id"]], score=False)
    with faked(world, Store(conn).get):
        run = sent(signed, noted)[0]["id"]
    with faked(world, Store(conn).get, delay=0.05):
        assert signed.post(f"/api/runs/{run}/scores", json={}).status_code == 202
        busy = signed.post(f"/api/runs/{run}/scores", json={})
        assert (busy.status_code, busy.json()) == (
            409,
            {"detail": f"run {run} has something under way", "code": "conflict"},
        )
        assert signed.post(f"/api/runs/{run}/halt").status_code == 204
        said = followed(signed, run)
    assert said[-1][1:] == ("done", {"halted": True})
    [scored] = [d for _, n, d in said if n == "run.scored"]
    assert "stopped" in {g["refused"] for g in scored["scores"]}
