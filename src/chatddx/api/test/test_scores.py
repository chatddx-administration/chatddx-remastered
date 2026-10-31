from dataclasses import replace
from uuid import uuid4

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatddx.api.state import AppState
from chatddx.api.test.helpers import (
    UNDER_WAY,
    asked,
    endpoint,
    family,
    followed,
    joined,
    names,
    sent,
    told,
    world_served,
)
from chatddx.bench import Bench
from chatddx.bench.test.helpers import ran, trial
from chatddx.curation import Plan
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import Queue, Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, QWEN, faked

__all__ = ["world_served"]


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
        assert (busy.status_code, busy.json()["detail"], busy.json()["code"]) == (
            409,
            f"run {run} has something under way",
            "conflict",
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


@pytest.mark.slow
def test_what_a_judge_is_asked_is_its_request_with_what_a_view_picks(
    signed: TestClient,
) -> None:
    noted = family(signed, "noted")
    [case] = signed.get(f"/api/families/{noted['id']}").json()["cases"]
    [expected] = case["expectations"]
    [verdict] = signed.get(
        "/api/threads", params={"kind": "judge", "name": "verdict"}
    ).json()
    judge = verdict["head"]["digest"]
    reads = "$.notes[?@.author == 'carol'].comment"
    body = {"judge": judge, "expectation": reads, "data": expected["data"]}
    got = signed.post("/api/judges/asked", json=body)
    assert got.status_code == 200, got.json()
    asked = got.json()
    [comment] = [
        n["comment"] for n in expected["data"]["notes"] if n["author"] == "carol"
    ]
    assert asked["picked"] == [comment]
    said = "".join(m["content"] for m in asked["request"]["messages"])
    assert comment in said and "‹completion›" in said
    assert asked["request"]["model"] == endpoint(signed, QWEN)["engine"]

    assert (
        signed.post("/api/judges/asked", json={**body, "expectation": "$["}).status_code
        == 422
    )
    elsewhere = {**body, "judge": expected["expectation"]}
    assert signed.post("/api/judges/asked", json=elsewhere).status_code == 404


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_field_is_measured_against_each_answer_as_it_is_written_and_nothing_is_written(
    signed: TestClient, bob: dict[str, str]
) -> None:
    noted = family(signed, "noted")
    made, _ = sent(signed, asked(signed, families=[noted["id"]]))
    [case] = signed.get(f"/api/families/{noted['id']}").json()["cases"]
    [expected] = case["expectations"]
    body = {
        "case": noted["case"],
        "expectation_schema": expected["expectation_schema"],
        "data": expected["data"],
        "field": "diagnosis",
    }
    got = signed.post("/api/expectations/measured", json=body)
    assert got.status_code == 200, got.json()
    assert got.headers["cache-control"] == "no-store"
    measured = got.json()
    assert measured["answers"] == 1
    assert measured["pattern"] == expected["data"]["diagnosis"]["pattern"]
    stored = {
        (g["score"], i["view"]): i["value"] for g in made["scores"] for i in g["items"]
    }
    told = 0
    for text in measured["texts"]:
        for seen in text["seen"]:
            assert seen["run"] == made["id"] and seen["replicate"] == 0
            score, _, replicate, view = seen["href"].split("/")[2:]
            assert (replicate, text["value"]) == ("0", stored[score, int(view)])
            told += 1
    assert told == measured["found"] + measured["missed"] + measured["unscored"] > 0

    missed = {**expected["data"], "diagnosis": {"pattern": "nothing & like & it"}}
    again = signed.post(
        "/api/expectations/measured", json={**body, "data": missed}
    ).json()
    assert (again["found"], again["missed"]) == (0, told)
    assert again["alternatives"] == [{"pattern": "nothing & like & it", "found": 0}]
    broken = {**expected["data"], "diagnosis": {"pattern": "(nothing"}}
    refused = signed.post(
        "/api/expectations/measured", json={**body, "data": broken}
    ).json()
    assert refused["problem"] and refused["alternatives"] == []
    assert len(
        signed.get(f"/api/runs/{made['id']}/scores", params={"all": True}).json()
    ) == len(made["scores"])
    elsewhere = signed.post("/api/expectations/measured", json=body, headers=bob)
    assert (elsewhere.status_code, elsewhere.json()["answers"]) == (200, 0)


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_how_a_case_fares_is_its_latest_runs_means_among_other_cases_drawn_or_not(
    signed: TestClient, served: FastAPI
) -> None:
    noted = family(signed, "noted")
    made, _ = sent(signed, asked(signed, families=[noted["id"]]))
    [case] = signed.get(f"/api/families/{noted['id']}").json()["cases"]
    [expected] = case["expectations"]
    path = f"/api/families/{noted['id']}/fared"
    query = {
        "case": noted["case"],
        "expectation_schema": expected["expectation_schema"],
    }
    got = signed.get(path, params=query)
    assert got.status_code == 200, got.json()
    assert got.headers["cache-control"] == "no-store"
    fared = got.json()
    assert fared["synthetic"] is False
    families = signed.get("/api/families").json()
    assert len(fared["cases"]) == len(families)
    assert fared["cases"][-1] == {
        "case": noted["case"],
        "family": noted["id"],
        "title": case["title"],
    }
    names = [c["name"] for c in fared["configurations"]]
    shown = [r for r in fared["rows"] if r["shown"]]
    assert shown and {names[r["configuration"]] for r in shown} == {LINES}
    stored = {
        (g["scorer"], i["view"]): i["value"]
        for g in made["scores"]
        for i in g["items"]
        if i["value"] is not None
    }
    for row in shown:
        metric = fared["metrics"][row["metric"]]
        assert row["shown"]["value"] == stored[metric["scorer"], metric["view"]]
        assert row["shown"]["synthetic"] is False
        [replicate] = row["shown"]["replicates"]
        assert replicate["value"] == row["shown"]["value"]
        assert replicate["href"].split("/")[2] in {g["score"] for g in made["scores"]}
    assert all(r["cases"] == [] for r in fared["rows"])
    behind = {
        c["name"]: [b["why"] for b in c["behind"]] for c in fared["configurations"]
    }
    assert behind[LINES] == ["not_whole"]
    assert fared["run"] is True

    held = served.state.chatddx
    assert isinstance(held, AppState)
    served.state.chatddx = replace(held, synthetic=3)
    try:
        drawn = signed.get(path, params=query).json()
    finally:
        served.state.chatddx = held
    assert drawn["synthetic"] is True
    last = len(drawn["cases"]) - 1
    for row in drawn["rows"]:
        assert len(row["cases"]) == last and last not in row["cases"]
        assert all(row["synthetic"]) and all(0 <= v <= 1 for v in row["values"])
    assert [
        r["shown"] for r in drawn["rows"] if r["shown"] and not r["shown"]["synthetic"]
    ] == [r["shown"] for r in shown]
