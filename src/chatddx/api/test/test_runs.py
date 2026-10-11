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
from chatddx.api.test.test_variations import OFF, PLAN_WEB, digest, thread
from chatddx.bench.test.sample import FREE_TEXT, QWEN
from chatddx.conftest import faked
from chatddx.core import settings
from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import Inventory
from chatddx.store import Store
from chatddx.store.store import Connection

pytestmark = pytest.mark.wip

GPT_OSS = "gpt-oss-20b@fake"
STREAM = {"Accept": "text/event-stream"}


@pytest.fixture
def served(db: str, world: Inventory) -> FastAPI:
    return app(
        world, Facts.load(BUNDLED), make_conninfo(settings.database(), dbname=db)
    )


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
    signed: TestClient, configuration: str = FREE_TEXT, **more: Any
) -> dict[str, Any]:
    return {
        "configuration": thread(signed, "configuration", configuration)["id"],
        "endpoint": QWEN,
        "families": [family(signed, "Dutchfall11w")["id"]],
        "seed": 7,
        **more,
    }


def events(text: str) -> list[tuple[str, dict[str, Any]]]:
    said: list[tuple[str, dict[str, Any]]] = []
    for block in text.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        said.append((fields["event"], json.loads(fields["data"])))
    return said


def finished(signed: TestClient, run: str) -> dict[str, Any]:
    for _ in range(500):
        shown = signed.get(f"/api/runs/{run}").json()
        if shown["finished"] and shown["scores"]:
            return shown
        time.sleep(0.02)
    raise AssertionError(f"run {run} wasn't finished and scored")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_is_answered_once_it_is_finished_and_scored(signed: TestClient) -> None:
    case = family(signed, "Dutchfall11w")["case"]
    got = signed.post("/api/runs", json=asked(signed))
    assert got.status_code == 201
    made = got.json()
    assert got.headers["location"] == f"/api/runs/{made['id']}"
    assert signed.get(got.headers["location"]).json() == made

    assert (made["endpoint"], made["cases"], made["seeds"]) == (QWEN, [case], [7])
    assert made["finished"] and made["finished_at"] is not None
    assert made["rig"]["distribution"] == "chatddx"
    [item] = made["items"]
    assert (item["case"], item["replicate"], item["outcome"]) == (case, 0, "completed")
    assert item["completion_tokens"] > 0
    graded = {g["name"]: g for g in made["scores"]}
    free = graded["free-text"]
    assert free["score"] is not None and free["refused"] is None
    assert free["labels"] == ["text", "differential", "dont-miss"]
    assert len(free["means"]) == 3
    assert {(s["case"], s["view"]) for s in free["items"]} == {
        (case, view) for view in range(3)
    }


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_streams_its_events_when_asked(signed: TestClient) -> None:
    case = family(signed, "Dutchfall11w")["case"]
    got = signed.post("/api/runs", json=asked(signed), headers=STREAM)
    assert got.status_code == 201
    assert got.headers["content-type"].startswith("text/event-stream")
    assert got.headers["cache-control"] == "no-cache"
    said = events(got.text)
    names = [name for name, _ in said]
    assert names[0] == "run.started"
    assert names[-2:] == ["run.finished", "run.scored"]
    assert {"item.started", "item.delta", "item.ended"} <= set(names)

    started = said[0][1]
    assert got.headers["location"] == f"/api/runs/{started['run']}"
    assert (started["cases"], started["seed"], started["greedy"]) == ([case], 7, False)
    content = [d for n, d in said if n == "item.delta" and d["kind"] == "content"]
    assert "".join(d["text"] for d in content).strip()
    assert content[-1]["tokens"] > 0
    [ended] = [d for n, d in said if n == "item.ended"]
    assert (ended["case"], ended["outcome"], ended["why"]) == (case, "completed", None)
    [scored] = [d for n, d in said if n == "run.scored"]
    shown = signed.get(got.headers["location"]).json()
    assert scored["scores"] == shown["scores"]


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_of_tags_runs_the_case_of_each_family_tagged(signed: TestClient) -> None:
    tagged = signed.get("/api/families", params={"tag": "edn"}).json()
    body = {**asked(signed), "families": None, "tags": ["edn"], "score": False}
    made = signed.post("/api/runs", json=body).json()
    assert sorted(i["case"] for i in made["items"]) == sorted(f["case"] for f in tagged)
    assert made["scores"] == []


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_run_the_gate_refuses_is_unprocessable_and_isn_t_recorded(
    signed: TestClient,
) -> None:
    for body, said in (
        (
            asked(signed, PLAN_WEB),
            "the skeleton's tools would get content from source sample",
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
    wrong: list[tuple[dict[str, Any], str]] = [
        ({"tags": ["edn"]}, "a run takes one of families, tags or cases"),
        ({"families": None}, "a run takes one of families, tags or cases"),
        ({"families": []}, "a run takes at least one case"),
        ({"families": [999]}, "no case 999 for alice"),
        ({"families": None, "tags": ["nowhere"]}, "no case tagged nowhere for alice"),
        ({"endpoint": "nowhere@fake"}, "no endpoint 'nowhere@fake' in the inventory"),
        ({"configuration": chunk["id"]}, f"no configuration {chunk['id']} for alice"),
        ({"parts": {"prompt": chunk["head"]["digest"]}}, "isn't a stored chunk"),
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
    first = signed.post("/api/runs", json=asked(signed)).json()
    second = signed.post(
        "/api/runs",
        json=asked(signed, seed=8, parts={"reasoning": off}, score=False),
    ).json()
    assert second["scores"] == []
    scorer = thread(signed, "scorer", "free-text", "archive")["head"]["digest"]

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
def test_a_run_s_items_hold_its_calls_and_render_again_as_they_were_sent(
    signed: TestClient,
) -> None:
    made = signed.post("/api/runs", json=asked(signed)).json()
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
    made = signed.post("/api/runs", json=asked(signed)).json()
    for path in ("", "/items", "/rendered-again"):
        got = signed.get(f"/api/runs/{made['id']}{path}", headers=bob)
        assert (got.status_code, got.json()) == (
            404,
            {"detail": f"no run {made['id']} of yours"},
        )
    assert signed.get("/api/runs", headers=bob).json() == []
    assert signed.get("/api/runs/not-a-run").status_code == 422


def test_runs_need_a_session(client: TestClient) -> None:
    run = "00000000-0000-0000-0000-000000000000"
    for path in ("/api/runs", f"/api/runs/{run}", f"/api/runs/{run}/items"):
        assert client.get(path).status_code == 401, path
    assert client.post("/api/runs", json={}).status_code == 401


@pytest.mark.slow
def test_the_stream_s_events_are_described(client: TestClient) -> None:
    described = client.get("/api/openapi.json").json()
    created = described["paths"]["/api/runs"]["post"]["responses"]["201"]
    assert set(created["content"]) == {"application/json", "text/event-stream"}
    assert "`run.started`" in created["description"]
    schemas = described["components"]["schemas"]
    assert {"RunStartedData", "ItemDeltaData", "RunScoredData"} <= set(schemas)


@pytest.mark.slow
def test_a_stream_its_client_leaves_halts_the_run_which_is_finished_and_scored(
    signed: TestClient,
    listening: str,
    world: Inventory,
    conn: Connection,
) -> None:
    body = asked(signed)
    alice = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=0.1),
        httpx2.Client(headers=alice) as http,
        http.stream(
            "POST", f"{listening}/api/runs", json=body, headers=STREAM, timeout=10
        ) as got,
    ):
        run = got.headers["location"].rsplit("/", 1)[1]
        for line in got.iter_lines():
            if line == "event: item.delta":
                break
    shown = finished(signed, run)
    [item] = shown["items"]
    assert item["outcome"] == "stopped"
    [item] = signed.get(f"/api/runs/{run}/items").json()
    assert item["call"]["error"] == "stopped"


@pytest.mark.slow
def test_a_request_its_client_leaves_halts_the_run_too(
    signed: TestClient,
    listening: str,
    world: Inventory,
    conn: Connection,
) -> None:
    body = asked(signed)
    alice = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=0.1),
        httpx2.Client(headers=alice) as http,
        pytest.raises(httpx2.ReadTimeout),
    ):
        _ = http.post(f"{listening}/api/runs", json=body, timeout=0.5)
    [run] = signed.get("/api/runs").json()
    shown = finished(signed, run["id"])
    [item] = shown["items"]
    assert item["outcome"] == "stopped"
