import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from chatddx.api.state import AppState
from chatddx.inventory import EndpointSpec

pytestmark = pytest.mark.wip

QWEN = "qwen3-8b-awq@fake"
GHOST = "sha256:" + "0" * 64


def test_endpoints_say_what_they_serve_and_what_they_re_cleared_for(
    signed: TestClient,
) -> None:
    listed = signed.get("/api/endpoints").json()
    assert [e["name"] for e in listed] == ["gpt-oss-20b@fake", QWEN]
    qwen = signed.get(f"/api/endpoints/{QWEN}").json()
    assert qwen == listed[1]
    assert (qwen["model"], qwen["url"], qwen["host"]) == (
        "Qwen/Qwen3-8B-AWQ",
        "http://127.0.0.1:12099/v1/",
        "fake",
    )
    assert (qwen["cleared_for"], qwen["max_jobs"], qwen["problem"]) == (
        ["sample", "typed"],
        4,
        None,
    )
    got = signed.get("/api/endpoints/nowhere@fake")
    assert got.status_code == 404
    assert got.json() == {"detail": "no endpoint 'nowhere@fake' in the inventory"}


def test_an_endpoint_whose_engine_isn_t_stored_says_so(
    served: FastAPI, signed: TestClient
) -> None:
    held = served.state.chatddx
    ghost = EndpointSpec(engine=GHOST, url=HttpUrl("http://127.0.0.1:1/v1/"))
    endpoints = {**held.inventory.endpoints, "ghost@nowhere": ghost}
    served.state.chatddx = AppState(
        held.conninfo,
        held.inventory.model_copy(update={"endpoints": endpoints}),
        held.facts,
    )
    shown = signed.get("/api/endpoints/ghost@nowhere").json()
    assert (shown["title"], shown["model"], shown["url"]) == (None, None, None)
    assert "isn't in the store" in shown["problem"]


def test_models_are_told_by_their_facts_with_the_endpoints_serving_them(
    signed: TestClient,
) -> None:
    models = {m["name"]: m for m in signed.get("/api/models").json()}
    assert models["Qwen/Qwen3-8B-AWQ"]["endpoints"] == [QWEN]
    assert models["openai/gpt-oss-20b"]["endpoints"] == ["gpt-oss-20b@fake"]
    assert all(m["facts"] is not None for m in models.values())


def test_a_component_is_shown_by_its_digest(signed: TestClient) -> None:
    [qwen] = [e for e in signed.get("/api/endpoints").json() if e["name"] == QWEN]
    shown = signed.get(f"/api/components/{qwen['engine']}").json()
    assert (shown["digest"], shown["kind"], shown["title"]) == (
        qwen["engine"],
        "engine.local",
        qwen["title"],
    )
    assert shown["body"]["kind"] == "engine.local"
    got = signed.get(f"/api/components/{GHOST}")
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no component {GHOST} in the store"},
    )


def test_every_read_needs_a_session(client: TestClient) -> None:
    for path in (
        "/api/threads?kind=configuration",
        "/api/threads/1",
        "/api/threads/1/edits",
        "/api/families",
        "/api/families/1",
        "/api/families/1/vignette",
        "/api/tags",
        "/api/endpoints",
        f"/api/endpoints/{QWEN}",
        "/api/models",
        f"/api/components/{GHOST}",
    ):
        assert client.get(path).status_code == 401, path
