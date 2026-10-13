from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.test_variations import thread
from chatddx.test.world import LINES, QWEN

pytestmark = pytest.mark.wip

CLINICIAN = "clinician (en)"


def body(signed: TestClient, found: dict[str, Any]) -> dict[str, Any]:
    return signed.get(f"/api/components/{found['head']['digest']}").json()["body"]


@pytest.mark.slow
def test_a_component_is_written_as_a_thread_of_one_s_own(signed: TestClient) -> None:
    archives = thread(signed, "instructions", CLINICIAN, "archive")
    held = body(signed, archives)
    asked = {
        "component": {**held, "text": "You are a careful physician."},
        "name": "careful",
        "language": "en",
    }

    got = signed.post("/api/threads", json=asked)
    assert got.status_code == 201
    made = got.json()
    assert got.headers["location"] == f"/api/threads/{made['id']}"
    assert (made["kind"], made["name"], made["owner"], made["language"]) == (
        "chunk.instructions",
        "careful",
        "alice",
        "en",
    )
    assert (made["forked_from"], made["findings"]) == (None, [])

    edits = f"/api/threads/{made['id']}/edits"
    terse = {"head": made["head"]["id"], "component": {**held, "text": "Be terse."}}
    got = signed.post(edits, json=terse)
    assert got.status_code == 201
    edited = got.json()
    assert signed.post(edits, json={**terse, "head": edited["id"]}).status_code == 200
    moved = signed.post(edits, json={**terse, "component": held})
    assert moved.status_code == 409

    fork = {"name": "svensk", "component": {**held, "text": "Var noggrann."}}
    got = signed.post(
        f"/api/threads/{archives['id']}/forks", json={**fork, "language": "sv"}
    )
    assert got.status_code == 201
    forked = got.json()
    assert (forked["forked_from"], forked["language"]) == (
        archives["head"]["id"],
        "sv",
    )


@pytest.mark.slow
def test_a_write_is_refused_what_isn_t_the_person_s(
    signed: TestClient, bob: dict[str, str]
) -> None:
    archives = thread(signed, "instructions", CLINICIAN, "archive")
    mine = thread(signed, "configuration", LINES)
    held = body(signed, archives)
    sampling = body(signed, thread(signed, "sampling", "greedy", "archive"))
    forks = f"/api/threads/{archives['id']}/forks"
    head = archives["head"]["id"]
    refusals: list[tuple[str, dict[str, Any], int, str]] = [
        (
            "/api/threads",
            {"component": {"kind": "tool"}, "name": "x"},
            422,
            "isn't a kind",
        ),
        (
            "/api/threads",
            {"component": sampling, "name": "x", "language": "en"},
            422,
            "chunk.sampling components have no language of their own",
        ),
        (
            "/api/threads",
            {"component": {**held, "text": 7}, "name": "x"},
            422,
            "validation error",
        ),
        (forks, {"name": "x", "parts": {"prompt": None}}, 422, "only a configuration"),
        (
            f"/api/threads/{mine['id']}/forks",
            {"name": "x", "component": held},
            422,
            "a configuration is written with parts, not a component",
        ),
        (
            f"/api/threads/{archives['id']}/edits",
            {"head": head},
            422,
            "an edit holds a component",
        ),
        (
            f"/api/threads/{archives['id']}/edits",
            {"head": head, "component": held},
            404,
            f"no instructions {archives['id']} of yours",
        ),
    ]
    for path, asked, status, said in refusals:
        got = signed.post(path, json=asked)
        assert got.status_code == status, (path, asked, got.json())
        assert said in got.json()["detail"]

    got = signed.post(forks, json={"name": "bob's"}, headers=bob)
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no instructions {archives['id']} for bob"},
    )


@pytest.mark.slow
def test_an_expectation_s_edit_says_what_the_lints_say(signed: TestClient) -> None:
    [family] = signed.get("/api/families", params={"name": "crlf"}).json()
    [expected] = signed.get(f"/api/families/{family['id']}").json()["expectations"]
    threads = signed.get(
        "/api/threads", params={"kind": "expectation", "owner": "alice"}
    )
    [mine] = [
        t for t in threads.json() if t["head"]["digest"] == expected["expectation"]
    ]
    held = body(signed, mine)
    got = signed.post(
        f"/api/threads/{mine['id']}/edits",
        json={"head": mine["head"]["id"], "component": {**held, "data": [1]}},
    )
    assert got.status_code == 201
    assert [f["code"] for f in got.json()["findings"]] == ["expectation.invalid"]

    got = signed.post(
        "/api/threads", json={"component": {**held, "data": [2]}, "name": "again"}
    )
    assert got.status_code == 422
    assert f"in thread {mine['id']}: edit that one" in got.json()["detail"]


@pytest.mark.slow
def test_a_recipe_of_one_s_making_is_a_new_configuration(signed: TestClient) -> None:
    def digest(kind: str, name: str) -> str:
        return thread(signed, kind, name, "archive")["head"]["digest"]

    recipe = {
        "instructions": digest("instructions", CLINICIAN),
        "prompt": digest("prompt", "case"),
        "output": digest("output", "native (en)"),
        "sampling": digest("sampling", "greedy"),
    }
    listed = signed.get("/api/threads", params={"kind": "configuration"}).json()
    got = signed.post("/api/threads", json={"recipe": recipe, "name": "my own"})
    assert got.status_code == 201
    made = got.json()
    assert made["head"]["digest"] not in {t["head"]["digest"] for t in listed}
    assert (made["kind"], made["owner"], made["forked_from"]) == (
        "skeleton",
        "alice",
        None,
    )
    assert {k: made["recipe"][k] for k in recipe} == recipe
    assert made["language"] == "en" and made["findings"] == []

    held = body(signed, thread(signed, "instructions", CLINICIAN, "archive"))
    for asked, said in (
        ({"recipe": recipe, "component": held}, "a component or a recipe, not both"),
        ({}, "a component or a recipe, not both"),
        ({"recipe": {**recipe, "prompt": recipe["output"]}}, "isn't a stored chunk"),
        ({"recipe": recipe, "language": "en"}, "comes from its recipe"),
        ({"recipe": {**recipe, "stack": "x"}}, "validation error"),
    ):
        got = signed.post("/api/threads", json={**asked, "name": "x"})
        assert got.status_code == 422, (asked, got.json())
        assert said in str(got.json()["detail"])


@pytest.mark.slow
def test_a_judge_is_written_over_a_judge_configuration(signed: TestClient) -> None:
    query = {"kind": "configuration", "purpose": "judge", "name": "judge (en)"}
    [judging] = signed.get("/api/threads", params={**query, "owner": "alice"}).json()
    engine = signed.get(f"/api/endpoints/{QWEN}").json()["engine"]
    judge = {
        "kind": "judge",
        "skeleton": judging["head"]["digest"],
        "engine": engine,
        "seeds": [1, 2],
    }
    got = signed.post("/api/threads", json={"component": judge, "name": "twice"})
    assert got.status_code == 201
    made = got.json()
    assert (made["kind"], made["owner"]) == ("judge", "alice")
    assert [f["code"] for f in made["findings"]] == ["judge.greedy_seeds"]

    generation = thread(signed, "configuration", LINES)["head"]["digest"]
    wrong = {**judge, "skeleton": generation}
    got = signed.post("/api/threads", json={"component": wrong, "name": "wrong"})
    assert got.status_code == 422
    assert "judge uses a generation skeleton" in got.json()["detail"]
