from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.helpers import asked, followed, names, told, world_served
from chatddx.inventory import Inventory
from chatddx.store import Store
from chatddx.store.queue import TAKEN_OUT
from chatddx.store.store import Connection
from chatddx.test.world import faked

__all__ = ["world_served"]


def job(signed: TestClient, run: str) -> dict[str, Any]:
    found = signed.get(f"/api/runs/{run}").json()["job"]
    assert found is not None
    return found


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_paused_queue_holds_a_run_a_stop_takes_it_out_and_it_resumes(
    signed: TestClient, bob: dict[str, str]
) -> None:
    paused = signed.patch("/api/queue", json={"paused": True}).json()
    assert (paused["paused"], paused["queued"], paused["under_way"]) == (True, 0, 0)
    run = signed.post("/api/runs", json=asked(signed)).json()["runs"][0]["run"]
    waiting = job(signed, run)
    assert (waiting["status"], waiting["ahead"], waiting["ended"]) == (
        "queued",
        None,
        None,
    )
    assert signed.get("/api/queue").json()["queued"] == 1
    assert signed.get("/api/queue", headers=bob).json()["queued"] == 0
    listed = signed.get("/api/runs").json()
    assert [r["job"]["status"] for r in listed] == ["queued"]

    stopped = signed.post("/api/queue/stop", json={}).json()
    assert stopped == {"taken_out": [run], "halting": []}
    taken = job(signed, run)
    assert (taken["status"], taken["why"]) == ("stopped", TAKEN_OUT)
    assert not signed.get(f"/api/runs/{run}").json()["finished"]
    assert names(followed(signed, run))[-1] == "done"

    resumed = signed.patch("/api/queue", json={"paused": False}).json()
    assert (resumed["paused"], resumed["queued"]) == (False, 0)
    got = signed.post(f"/api/runs/{run}/resume", json={"score": False})
    assert got.status_code == 202, got.json()
    assert got.headers["location"] == f"/api/runs/{run}"
    assert got.json()["run"] == run
    said = followed(signed, run)
    assert names(said)[-2:] == ["run.finished", "done"]
    shown = signed.get(f"/api/runs/{run}").json()
    assert shown["finished"] and shown["job"]["status"] == "finished"
    assert shown["scores"] == []
    assert signed.get("/api/queue").json()["workers"] >= 1

    again = signed.post(f"/api/runs/{run}/resume", json={})
    assert (again.status_code, again.json()) == (
        422,
        {"detail": f"run {run} is finished", "code": "refused"},
    )
    theirs = signed.post(f"/api/runs/{run}/resume", json={}, headers=bob)
    assert theirs.status_code == 404


@pytest.mark.slow
def test_stopping_now_halts_what_is_under_way(
    signed: TestClient, listening: str, world: Inventory, conn: Connection
) -> None:
    bearer = {"Authorization": signed.headers["Authorization"]}
    with (
        faked(world, Store(conn).get, delay=0.1),
        httpx2.Client(headers=bearer) as http,
    ):
        run = signed.post("/api/runs", json=asked(signed)).json()["runs"][0]["run"]
        with http.stream(
            "GET", f"{listening}/api/runs/{run}/events", timeout=30
        ) as got:
            lines = got.iter_lines()
            read: list[str] = []
            for line in lines:
                read.append(line)
                if line == "event: item.delta":
                    break
            assert signed.post("/api/queue/stop", json={}).json() == {
                "taken_out": [],
                "halting": [],
            }
            stopped = signed.post("/api/queue/stop", json={"now": True}).json()
            assert stopped == {"taken_out": [], "halting": [run]}
            said = told("\n".join([*read, *lines]))
    assert said[-1][1:] == ("done", {"halted": True})
    shown = signed.get(f"/api/runs/{run}").json()
    assert shown["finished"] and shown["scores"] == []
    assert (shown["job"]["status"], shown["job"]["halt"]) == ("stopped", True)
    [item] = shown["items"]
    assert item["outcome"] == "stopped"
