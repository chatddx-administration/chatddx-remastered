import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from chatddx.api.state import AppState
from chatddx.inventory import EndpointSpec, Inventory
from chatddx.test.world import (
    GPT_OSS,
    GPT_OSS_MODEL,
    MISTRAL,
    MISTRAL_MODEL,
    QWEN,
    QWEN_BARE,
    QWEN_MODEL,
    REMOTE,
    TEST,
)

pytestmark = pytest.mark.solidified

GHOST = "sha256:" + "0" * 64


def test_endpoints_say_what_they_serve_and_what_they_re_cleared_for(
    signed: TestClient,
) -> None:
    inventory = Inventory.load(TEST / "inventory.toml")
    listed = signed.get("/api/endpoints").json()
    assert [e["name"] for e in listed] == sorted(inventory.endpoints)
    for shown in listed:
        name = shown["name"]
        spec = inventory.endpoint(name)
        assert signed.get(f"/api/endpoints/{name}").json() == shown
        assert (shown["engine"], shown["host"], shown["max_jobs"]) == (
            spec.engine,
            spec.host,
            spec.max_jobs,
        )
        assert (shown["credential"], shown["cleared_for"], shown["problem"]) == (
            spec.credential,
            sorted(inventory.cleared_for(name)),
            None,
        )

    endpoints = {e["name"]: e for e in listed}
    qwen, remote = endpoints[QWEN], endpoints[REMOTE]
    assert (qwen["model"], qwen["url"], qwen["cleared_for"]) == (
        QWEN_MODEL,
        str(inventory.endpoint(QWEN).url),
        sorted(inventory.sources),
    )
    engine = signed.get(f"/api/components/{remote['engine']}").json()["body"]
    assert (remote["model"], remote["url"], remote["host"]) == (
        engine["model"],
        str(inventory.endpoint(REMOTE).url),
        None,
    )
    assert remote["credential"] is not None and remote["cleared_for"] == []
    got = signed.get("/api/endpoints/nowhere@fake")
    assert got.status_code == 404
    assert got.json() == {
        "detail": "no endpoint 'nowhere@fake' in the inventory",
        "code": "not_found",
    }


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
    assert models[QWEN_MODEL]["endpoints"] == [QWEN_BARE, QWEN]
    assert models[GPT_OSS_MODEL]["endpoints"] == [GPT_OSS]
    assert models[MISTRAL_MODEL]["endpoints"] == [MISTRAL]
    assert models[MISTRAL_MODEL]["facts"]["family"] == "mistral"
    unknown = signed.get(f"/api/endpoints/{REMOTE}").json()["model"]
    assert models[unknown]["endpoints"] == [REMOTE]
    assert [m for m, held in models.items() if held["facts"] is None] == [unknown]


def test_a_component_is_shown_by_its_digest(signed: TestClient) -> None:
    endpoints = {e["name"]: e for e in signed.get("/api/endpoints").json()}
    for name, kind in ((QWEN, "engine.local"), (REMOTE, "engine.remote")):
        endpoint = endpoints[name]
        shown = signed.get(f"/api/components/{endpoint['engine']}").json()
        assert (shown["digest"], shown["kind"], shown["title"]) == (
            endpoint["engine"],
            kind,
            endpoint["title"],
        )
        assert shown["body"]["kind"] == kind
    got = signed.get(f"/api/components/{GHOST}")
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no component {GHOST} in the store", "code": "not_found"},
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
