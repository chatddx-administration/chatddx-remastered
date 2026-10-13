import json
import socket
import threading
import time
from collections.abc import Iterator
from typing import Any

import httpx2
import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg.conninfo import make_conninfo

from chatddx.api.app import app
from chatddx.api.test.test_variations import digest, thread
from chatddx.core import settings
from chatddx.inventory import Inventory
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import (
    GPT_OSS,
    LINES,
    NATIVE_TOOLS,
    OFF,
    QWEN,
    faked,
    world_facts,
)

pytestmark = pytest.mark.solidified

type Told = list[tuple[int, str, dict[str, Any]]]


@pytest.fixture
def served(db: str, world: Inventory) -> FastAPI:
    return app(world, world_facts(), make_conninfo(settings.database(), dbname=db))


@pytest.fixture
def listening(served: FastAPI) -> Iterator[str]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
    server = uvicorn.Server(
        uvicorn.Config(served, host="127.0.0.1", port=port, log_level="warning")
    )
    running = threading.Thread(target=server.run, daemon=True)
    running.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    running.join(5)


def family(signed: TestClient, name: str) -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": name}).json()
    return found


def asked(
    signed: TestClient, configuration: str = LINES, **more: Any
) -> dict[str, Any]:
    return {
        "configuration": thread(signed, "configuration", configuration)["id"],
        "endpoint": QWEN,
        "families": [family(signed, "crlf")["id"]],
        "seed": 7,
        **more,
    }


def told(text: str) -> Told:
    said: Told = []
    for block in text.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        said.append((int(fields["id"]), fields["event"], json.loads(fields["data"])))
    return said


def followed(signed: TestClient, run: str, **headers: str) -> Told:
    got = signed.get(f"/api/runs/{run}/events", headers=headers)
    assert got.status_code == 200, got.text
    assert got.headers["content-type"].startswith("text/event-stream")
    return told(got.text)


def sent(signed: TestClient, body: dict[str, Any]) -> tuple[dict[str, Any], Told]:
    got = signed.post("/api/runs", json=body)
    assert got.status_code == 202, got.json()
    said = followed(signed, got.json()["run"])
    return signed.get(got.headers["location"]).json(), said


def names(said: Told) -> list[str]:
    return [name for _, name, _ in said]


def finished(signed: TestClient, run: str) -> dict[str, Any]:
    for _ in range(500):
        shown = signed.get(f"/api/runs/{run}").json()
        if shown["finished"] and shown["scores"]:
            return shown
        time.sleep(0.02)
    raise AssertionError(f"run {run} wasn't finished and scored")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_is_accepted_and_told_by_its_events(signed: TestClient) -> None:
    case = family(signed, "crlf")["case"]
    got = signed.post("/api/runs", json=asked(signed))
    assert got.status_code == 202
    started = got.json()
    assert got.headers["location"] == f"/api/runs/{started['run']}"
    assert (started["endpoint"], started["cases"]) == (QWEN, [case])
    assert (started["seed"], started["greedy"]) == (7, False)

    said = followed(signed, started["run"])
    ids = [i for i, _, _ in said]
    assert ids == sorted(set(ids)) and ids[0] == 1
    assert said[0][1:] == ("run.started", started)
    assert names(said)[-2:] == ["run.scored", "done"]
    assert said[-1][2] == {"halted": False}
    expected = {"item.started", "item.ended", "run.finished", "run.scoring"}
    assert expected | {"score.started", "score.item"} <= set(names(said))
    [ended] = [d for _, n, d in said if n == "item.ended"]
    assert (ended["case"], ended["outcome"], ended["why"]) == (case, "completed", None)

    made = signed.get(got.headers["location"]).json()
    assert (made["endpoint"], made["cases"], made["seeds"]) == (QWEN, [case], [7])
    assert made["finished"] and made["finished_at"] is not None
    assert made["rig"]["distribution"] == "chatddx"
    [item] = made["items"]
    assert (item["case"], item["replicate"], item["outcome"]) == (case, 0, "completed")
    assert item["completion_tokens"] > 0
    [scored] = [d for _, n, d in said if n == "run.scored"]
    assert scored["scores"] == made["scores"]
    graded = {g["name"]: g for g in made["scores"]}
    lines = graded["lines"]
    assert lines["score"] is not None and lines["refused"] is None
    assert lines["labels"] == ["text", "differential", "dont-miss"]
    assert {(s["case"], s["view"]) for s in lines["items"]} == {
        (case, view) for view in range(3)
    }
    [scoring] = [d for _, n, d in said if n == "run.scoring"]
    assert {s["name"] for s in scoring["scorers"]} == set(graded)


@pytest.mark.slow
def test_a_run_s_events_stream_as_they_come_and_resume_after_an_id(
    signed: TestClient, world: Inventory, conn: Connection
) -> None:
    with faked(world, Store(conn).get, delay=0.01):
        run = signed.post("/api/runs", json=asked(signed, score=False)).json()["run"]
        said = followed(signed, run)
    content = [d for _, n, d in said if n == "item.delta" and d["kind"] == "content"]
    assert "".join(d["text"] for d in content).strip()
    assert content[-1]["tokens"] > 0
    assert names(said)[-2:] == ["run.finished", "done"]

    again = followed(signed, run)
    assert again == [s for s in said if s[1] != "item.delta"]
    middle = again[len(again) // 2][0]
    assert followed(signed, run, **{"Last-Event-ID": str(middle)}) == [
        s for s in again if s[0] > middle
    ]


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_with_nothing_under_way_here_is_told_from_the_ledger(
    signed: TestClient, db: str, world: Inventory
) -> None:
    made, said = sent(signed, asked(signed))
    elsewhere = app(world, world_facts(), make_conninfo(settings.database(), dbname=db))
    with TestClient(elsewhere, base_url="https://testserver") as other:
        other.headers.update(signed.headers)
        recorded = followed(other, made["id"])
    live = [s for s in said if s[1] in {"item.started", "item.ended", "run.finished"}]
    assert [s[1:] for s in recorded if s[1] in {n for _, n, _ in live}] == [
        s[1:] for s in live
    ]
    assert recorded[0][1:] == said[0][1:]
    assert recorded[-2][1:] == ("run.scored", {"scores": made["scores"]})
    assert recorded[-1][1:] == ("done", {"halted": None})


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_of_tags_runs_the_case_of_each_family_tagged(signed: TestClient) -> None:
    tagged = signed.get("/api/families", params={"tag": "swedish"}).json()
    body = {**asked(signed), "families": None, "tags": ["swedish"], "score": False}
    made, said = sent(signed, body)
    assert sorted(i["case"] for i in made["items"]) == sorted(f["case"] for f in tagged)
    assert made["scores"] == [] and "run.scoring" not in names(said)


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_the_gate_refuses_is_unprocessable_and_isn_t_recorded(
    signed: TestClient,
) -> None:
    for body, said in (
        (
            asked(signed, NATIVE_TOOLS),
            "the skeleton's tools would get content from source test",
        ),
        ({**asked(signed), "endpoint": GPT_OSS}, f"endpoint '{GPT_OSS}' can't be"),
    ):
        got = signed.post("/api/runs", json=body)
        assert got.status_code == 422
        assert said in got.json()["detail"]
    assert signed.get("/api/runs").json() == []


@pytest.mark.slow
def test_a_run_the_request_names_wrong_is_unprocessable(signed: TestClient) -> None:
    good = asked(signed)
    chunk = thread(signed, "reasoning", OFF)
    query = {"kind": "configuration", "purpose": "judge", "name": "judge (en)"}
    judge = signed.get("/api/threads", params={**query, "owner": "alice"}).json()[0]
    wrong: list[tuple[dict[str, Any], str]] = [
        ({"tags": ["swedish"]}, "a run takes one of families, tags or cases"),
        ({"families": None}, "a run takes one of families, tags or cases"),
        ({"families": []}, "a run takes at least one case"),
        ({"families": [999]}, "no case 999 for alice"),
        ({"families": None, "tags": ["nowhere"]}, "no case tagged nowhere for alice"),
        ({"endpoint": "nowhere@fake"}, "no endpoint 'nowhere@fake' in the inventory"),
        ({"configuration": chunk["id"]}, f"no configuration {chunk['id']} for alice"),
        ({"parts": {"prompt": chunk["head"]["digest"]}}, "isn't a stored chunk"),
        ({"configuration": judge["id"]}, "judge (en) is a judge configuration"),
    ]
    for changed, said in wrong:
        got = signed.post("/api/runs", json={**good, **changed})
        assert got.status_code == 422, changed
        assert said in json.dumps(got.json()["detail"])
    assert signed.get("/api/runs").json() == []


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_runs_are_listed_newest_first_and_filtered(signed: TestClient) -> None:
    off = digest(signed, "reasoning", OFF)
    first, _ = sent(signed, asked(signed))
    second, _ = sent(
        signed, asked(signed, seed=8, parts={"reasoning": off}, score=False)
    )
    assert second["scores"] == []
    scorer = thread(signed, "scorer", "lines", "archive")["head"]["digest"]

    def listed(**params: Any) -> list[str]:
        return [r["id"] for r in signed.get("/api/runs", params=params).json()]

    assert listed() == [second["id"], first["id"]]
    assert listed(limit=1) == [second["id"]]
    assert listed(offset=1) == [first["id"]]
    assert listed(trial=first["trial"]) == [first["id"]]
    assert listed(reaching=second["skeleton"]) == [second["id"]]
    assert listed(reaching=first["cases"][0]) == [second["id"], first["id"]]
    assert listed(scored_by=scorer) == [first["id"]]
    [shown] = signed.get("/api/runs", params={"limit": 1, "offset": 1}).json()
    assert shown == {k: first[k] for k in shown}
    assert signed.get("/api/runs", params={"limit": 0}).status_code == 422


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_no_browser_keeps_what_is_case_derived(signed: TestClient) -> None:
    made, _ = sent(signed, asked(signed))
    run, [score, *_] = made["id"], made["scores"]
    kept = {
        path: signed.get(path).headers.get("cache-control")
        for path in (
            f"/api/runs/{run}",
            f"/api/runs/{run}/items",
            f"/api/runs/{run}/events",
            f"/api/runs/{run}/scores/{score['score']}",
            f"/api/runs/{run}/scores/{score['score']}/items",
            f"/api/families/{family(signed, 'crlf')['id']}/vignette",
        )
    }
    assert [path for path, said in kept.items() if said == "no-store"] == [
        f"/api/runs/{run}/items",
        f"/api/runs/{run}/events",
        f"/api/runs/{run}/scores/{score['score']}/items",
        f"/api/families/{family(signed, 'crlf')['id']}/vignette",
    ]


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_s_items_hold_its_calls_and_render_again_as_they_were_sent(
    signed: TestClient,
) -> None:
    made, _ = sent(signed, asked(signed))
    [item] = signed.get(f"/api/runs/{made['id']}/items").json()
    assert {k: item[k] for k in made["items"][0]} == made["items"][0]
    assert item["why"] is None and item["turns"] == []
    assert item["call"]["response"]["choices"]
    assert item["vignette"]["hex"]

    [again] = signed.get(f"/api/runs/{made['id']}/rendered-again").json()
    assert again == {
        "case": item["case"],
        "replicate": 0,
        "same": True,
        "why": None,
    }


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_another_s_run_isn_t_found(signed: TestClient, bob: dict[str, str]) -> None:
    made, _ = sent(signed, asked(signed))
    for path in ("", "/items", "/rendered-again", "/events"):
        got = signed.get(f"/api/runs/{made['id']}{path}", headers=bob)
        assert (got.status_code, got.json()) == (
            404,
            {"detail": f"no run {made['id']} of yours", "code": "not_found"},
        )
    got = signed.post(f"/api/runs/{made['id']}/halt", headers=bob)
    assert got.status_code == 404
    assert signed.get("/api/runs", headers=bob).json() == []
    assert signed.get("/api/runs/not-a-run").status_code == 422


def test_runs_need_a_session(client: TestClient) -> None:
    run = "00000000-0000-0000-0000-000000000000"
    for path in ("", f"/{run}", f"/{run}/items", f"/{run}/events"):
        assert client.get(f"/api/runs{path}").status_code == 401, path
    assert client.post("/api/runs", json={}).status_code == 401
    assert client.post(f"/api/runs/{run}/halt").status_code == 401


@pytest.mark.slow
def test_the_events_are_described(client: TestClient) -> None:
    described = client.get("/api/openapi.json").json()
    paths = described["paths"]
    assert "202" in paths["/api/runs"]["post"]["responses"]
    told = paths["/api/runs/{run}/events"]["get"]["responses"]["200"]
    assert set(told["content"]) == {"text/event-stream"}
    assert "`run.started`" in told["description"] and "`done`" in told["description"]
    schemas = described["components"]["schemas"]
    expected = {"RunStartedData", "ItemDeltaData", "RunScoredData", "DoneData"}
    assert expected | {"ScoreStartedData", "JudgeAnsweredData"} <= set(schemas)


@pytest.mark.slow
def test_a_halt_stops_a_run_which_is_finished_and_left_to_score(
    signed: TestClient, listening: str, world: Inventory, conn: Connection
) -> None:
    alice = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=0.1),
        httpx2.Client(headers=alice) as http,
    ):
        run = signed.post("/api/runs", json=asked(signed)).json()["run"]
        with http.stream(
            "GET", f"{listening}/api/runs/{run}/events", timeout=10
        ) as got:
            lines = got.iter_lines()
            for line in lines:
                if line == "event: item.delta":
                    break
            assert signed.post(f"/api/runs/{run}/halt").status_code == 204
            rest = "\n".join(lines)
    said = told(rest[rest.index("id: ") :])
    assert names(said)[-2:] == ["run.finished", "done"]
    assert said[-1][2] == {"halted": True}
    shown = signed.get(f"/api/runs/{run}").json()
    [item] = shown["items"]
    assert (item["outcome"], shown["finished"], shown["scores"]) == (
        "stopped",
        True,
        [],
    )
    got = signed.post(f"/api/runs/{run}/halt")
    assert (got.status_code, got.json()) == (
        409,
        {"detail": f"run {run} has nothing under way", "code": "conflict"},
    )


@pytest.mark.slow
def test_a_run_whose_listener_goes_away_goes_on(
    signed: TestClient, listening: str, world: Inventory, conn: Connection
) -> None:
    alice = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=0.02),
        httpx2.Client(headers=alice) as http,
    ):
        run = signed.post("/api/runs", json=asked(signed)).json()["run"]
        with http.stream(
            "GET", f"{listening}/api/runs/{run}/events", timeout=10
        ) as got:
            for line in got.iter_lines():
                if line == "event: item.delta":
                    break
        shown = finished(signed, run)
    [item] = shown["items"]
    assert item["outcome"] == "completed"
