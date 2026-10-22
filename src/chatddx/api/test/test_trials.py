from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.helpers import (
    endpoint,
    family,
    followed,
    names,
    thread,
    world_served,
)
from chatddx.test.world import LINES_GUIDED, QWEN

__all__ = ["world_served"]


def composed(signed: TestClient, *families: str) -> dict[str, Any]:
    return {
        "kind": "trial",
        "skeleton": thread(signed, "configuration", LINES_GUIDED)["head"]["digest"],
        "engine": endpoint(signed, QWEN)["engine"],
        "cases": [family(signed, f)["case"] for f in families],
        "seeds": [7],
    }


def trial(signed: TestClient, name: str, *families: str) -> dict[str, Any]:
    body = {"component": composed(signed, *families), "name": name}
    got = signed.post("/api/threads", json=body)
    assert got.status_code == 201, got.json()
    return got.json()


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_trials_are_written_in_their_cases_language_and_run_as_one_start(
    signed: TestClient,
) -> None:
    english, swedish = trial(signed, "english", "crlf"), trial(signed, "swedish", "nfd")
    assert (english["language"], swedish["language"]) == ("en", "sv")
    listed = signed.get("/api/threads", params={"kind": "trial", "owner": "alice"})
    assert {t["name"] for t in listed.json()} == {"english", "swedish"}

    versions = [english["head"]["id"], swedish["head"]["id"]]
    body = {"trials": versions, "concurrency": 2, "score": False}
    got = signed.post("/api/runs/trials", json=body)
    assert got.status_code == 202, got.json()
    first, second = got.json()["runs"]
    assert got.headers["location"] == f"/api/runs/{first['run']}"
    assert (first["trial"], second["trial"]) == (
        english["head"]["digest"],
        swedish["head"]["digest"],
    )
    for run in (first, second):
        assert names(followed(signed, run["run"]))[-1] == "done"
    listed = signed.get("/api/runs", params={"with": first["run"]}).json()
    assert {(r["id"], r["described"], r["started_with"]) for r in listed} == {
        (first["run"], "english × qwen3-8b-awq × crlf (greedy)", None),
        (
            second["run"],
            "swedish × qwen3-8b-awq × nfd, in sv, translated (greedy)",
            first["run"],
        ),
    }

    mixed = {"component": composed(signed, "crlf", "nfd"), "name": "mixed"}
    got = signed.post("/api/threads", json=mixed)
    assert got.status_code == 422
    assert (
        got.json()["detail"] == "a trial's cases are in one language, not in en and sv"
    )
    configuration = thread(signed, "configuration", LINES_GUIDED)["head"]["id"]
    got = signed.post("/api/runs/trials", json={"trials": [configuration]})
    assert got.status_code == 404
