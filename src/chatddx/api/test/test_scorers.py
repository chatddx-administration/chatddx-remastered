import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.test_variations import thread
from chatddx.api.test.test_writes import body
from chatddx.test.world import LINES

pytestmark = pytest.mark.wip

PATTERNS = "chatddx.scorers.patterns:score"


def test_the_scoring_code_shipped_is_listed_with_what_its_metrics_take(
    signed: TestClient,
) -> None:
    [code] = signed.get("/api/scorer-code").json()
    assert (code["entry_point"], code["version"]) == (PATTERNS, 1)
    assert [m["name"] for m in code["metrics"]] == [
        "first_mention",
        "mentions",
        "reciprocal_rank",
    ]
    nothing = {"type": "object", "additionalProperties": False}
    assert all(m["params"] == nothing and m["measures"] for m in code["metrics"])
    assert code["params"] == nothing


@pytest.mark.slow
def test_a_scorer_is_written_with_its_labels(signed: TestClient) -> None:
    archives = thread(signed, "scorer", "list", "archive")
    assert archives["head"]["labels"] == {
        "views": ["differential", "dont-miss"],
        "resources": [],
    }
    held = body(signed, archives)

    got = signed.post(f"/api/threads/{archives['id']}/forks", json={"name": "mine"})
    assert got.status_code == 201
    fork = got.json()
    assert fork["head"]["digest"] == archives["head"]["digest"]
    assert fork["head"]["labels"] == archives["head"]["labels"]

    edits = f"/api/threads/{fork['id']}/edits"
    renamed = {"views": ["ddx", None]}
    asked = {"head": fork["head"]["id"], "component": held, "labels": renamed}
    got = signed.post(edits, json=asked)
    assert got.status_code == 201
    edited = got.json()
    assert edited["digest"] == fork["head"]["digest"]
    assert edited["labels"] == {"views": ["ddx"], "resources": []}
    again = {**asked, "head": edited["id"]}
    assert signed.post(edits, json=again).status_code == 200
    history = signed.get(edits).json()
    assert [e["labels"]["views"] for e in history] == [
        ["differential", "dont-miss"],
        ["ddx"],
    ]
    assert thread(signed, "scorer", "list", "archive") == archives

    one = {**held, "views": held["views"][:1]}
    got = signed.post(
        "/api/threads",
        json={"component": one, "name": "narrow", "labels": {"views": ["first"]}},
    )
    assert got.status_code == 201
    assert got.json()["head"]["labels"] == {"views": ["first"], "resources": []}


@pytest.mark.slow
def test_a_scorer_that_could_never_score_is_refused(signed: TestClient) -> None:
    archives = thread(signed, "scorer", "whole", "archive")
    held = body(signed, archives)
    [view] = held["views"]
    instructions = thread(signed, "instructions", "clinician (en)", "archive")
    configuration = thread(signed, "configuration", LINES)
    for at, asked, said in (
        (
            "/api/threads",
            {
                "component": {**held, "views": [{**view, "metric": "recall"}]},
                "name": "x",
            },
            "knows no metric recall",
        ),
        (
            "/api/threads",
            {"component": {**held, "version": 2}, "name": "x"},
            "is at version 1",
        ),
        (
            "/api/threads",
            {"component": held, "name": "x", "labels": {"views": ["a", "b"]}},
            "has no view at position 1",
        ),
        (
            f"/api/threads/{instructions['id']}/forks",
            {"name": "x", "labels": {"views": ["a"]}},
            "only a scorer's views and resources have labels",
        ),
        (
            f"/api/threads/{configuration['id']}/forks",
            {"name": "x", "labels": {"views": ["a"]}},
            "only a scorer has labels",
        ),
    ):
        got = signed.post(at, json=asked)
        assert (got.status_code, said in got.json()["detail"]) == (422, True), (
            got.json()
        )
