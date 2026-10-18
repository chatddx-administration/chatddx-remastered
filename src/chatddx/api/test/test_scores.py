from uuid import uuid4

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.api.app import app
from chatddx.api.test.test_runs import (
    UNDER_WAY,
    asked,
    family,
    followed,
    joined,
    names,
    sent,
    told,
)
from chatddx.bench import Bench
from chatddx.bench.test.helpers import ran, trial
from chatddx.curation import Plan
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import Queue, Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, faked


@pytest.fixture
def served(db: str, world: Inventory) -> FastAPI:
    conninfo = make_conninfo(settings.database(), dbname=db)
    return app(world, conninfo, worker=True)


@pytest.mark.slow
def test_a_run_s_scores_are_read_with_their_items_and_judge_calls(
    signed: TestClient,
    bob: dict[str, str],
    world: Inventory,
    conn: Connection,
    alice: Person,
    listening: str,
) -> None:
    noted = family(signed, "noted")["id"]
    with faked(world, Store(conn).get):
        made, _ = sent(signed, asked(signed, families=[noted]))
    run = made["id"]
    latest = signed.get(f"/api/runs/{run}/scores").json()
    assert latest == made["scores"]
    judged = next(g for g in latest if g["name"] == "judged")
    assert judged["finished"] and judged["scoring"] and judged["at"]
    path = f"/api/runs/{run}/scores/{judged['score']}"

    shown = signed.get(f"{path}/items").json()
    views = {i["view"]: i for i in shown["items"]}
    assert sorted(views) == [0, 1, 2, 3]
    assert views[0]["judge_calls"] == []
    assert [len(views[v]["judge_calls"]) for v in (1, 2, 3)] == [1, 1, 3]
    assert views[3]["detail"] is not None
    assert shown["findings"] == []

    queue = Queue(conn)
    queue.pause(alice.id)
    bearer = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=UNDER_WAY),
        httpx2.Client(headers=bearer) as http,
    ):
        got = signed.post(f"/api/runs/{run}/scores", json={})
        assert got.status_code == 202
        said = joined(http, listening, run, lambda: queue.pause(alice.id, False))
    assert got.headers["location"] == f"/api/runs/{run}/scores"
    assert {s["name"] for s in got.json()["scorers"]} == {g["name"] for g in latest}
    after = names(said)[names(said).index("run.scoring") :]
    assert "run.finished" in names(said)[: -len(after)]
    assert after[-2:] == ["run.scored", "done"]
    assert {"score.started", "score.item", "judge.asked", "judge.answered"} <= set(
        after
    )
    asked_ = [d for _, n, d in said if n == "judge.asked"]
    assert len(asked_) == 5 and {d["view"] for d in asked_} == {1, 2, 3}
    every = signed.get(f"/api/runs/{run}/scores", params={"all": "true"}).json()
    again = signed.get(f"/api/runs/{run}/scores").json()
    assert len(every) == 2 * len(latest)
    assert {g["score"] for g in every[: len(latest)]} == {g["score"] for g in again}
    assert judged in every

    assert signed.get(f"/api/runs/{run}/scores", headers=bob).status_code == 404
    assert signed.get(f"{path}/items", headers=bob).status_code == 404
    gone = signed.get(f"/api/runs/{run}/scores/{uuid4()}/items")
    assert gone.status_code == 404


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
    _ = bench.score(bench.run(left), {lines})
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
    listening: str,
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
    queue = Queue(conn)
    queue.pause(alice.id)
    bearer = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=0.05),
        httpx2.Client(headers=bearer) as http,
    ):
        assert signed.post(f"/api/runs/{run}/scores", json={}).status_code == 202
        busy = signed.post(f"/api/runs/{run}/scores", json={})
        assert (busy.status_code, busy.json()) == (
            409,
            {"detail": f"run {run} has something under way", "code": "conflict"},
        )
        events = f"{listening}/api/runs/{run}/events"
        with http.stream("GET", events, timeout=30) as got:
            lines = got.iter_lines()
            read = [next(lines)]
            queue.pause(alice.id, False)
            for line in lines:
                read.append(line)
                if line == "event: judge.asked":
                    break
            assert signed.post(f"/api/runs/{run}/halt").status_code == 204
            said = told("\n".join([*read, *lines]))
    assert said[-1][1:] == ("done", {"halted": True})
    assert 1 <= names(said).count("judge.asked") < 5
    [scored] = [d for _, n, d in said if n == "run.scored"]
    assert {g["name"] for g in scored["scores"]} == {"lines", "whole", "judged"}


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_scorer_is_tried_on_a_case_s_answers_as_it_is_typed_and_nothing_is_written(
    signed: TestClient, bob: dict[str, str]
) -> None:
    noted = family(signed, "noted")
    made, _ = sent(signed, asked(signed, families=[noted["id"]]))
    run = made["id"]
    [case] = signed.get(f"/api/families/{noted['id']}").json()["cases"]
    [expected] = case["expectations"]
    judged = next(g for g in made["scores"] if g["name"] == "judged")
    scorer = signed.get(f"/api/components/{judged['scorer']}").json()["body"]
    body = {
        "scorer": scorer,
        "expectation": expected["data"],
        "case": noted["case"],
        "runs": [run],
    }
    got = signed.post("/api/scorers/try", json=body)
    assert got.status_code == 200, got.json()
    assert got.headers["cache-control"] == "no-store"
    [tried] = got.json()
    assert (tried["run"], tried["replicate"]) == (run, 0)
    stored = {i["view"]: i["value"] for i in judged["items"]}
    views = scorer["views"]
    for at, (view, said) in enumerate(zip(views, tried["views"], strict=True)):
        assert said["judged"] == (view.get("judge") is not None)
        assert said["value"] == (None if said["judged"] else stored[at])

    missed = {**expected["data"], "diagnosis": {"pattern": "nothing & like & it"}}
    again = signed.post("/api/scorers/try", json={**body, "expectation": missed})
    [unjudged, *_] = [v for v in again.json()[0]["views"] if not v["judged"]]
    assert unjudged["value"] == 0.0
    assert len(
        signed.get(f"/api/runs/{run}/scores", params={"all": True}).json()
    ) == len(made["scores"])

    unknown = {**scorer, "views": [{**views[0], "metric": "nothing"}]}
    refused = signed.post("/api/scorers/try", json={**body, "scorer": unknown})
    assert refused.status_code == 422 and "nothing" in refused.json()["detail"]
    assert signed.post("/api/scorers/try", json=body, headers=bob).status_code == 404
