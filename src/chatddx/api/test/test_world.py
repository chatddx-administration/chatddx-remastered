import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from chatddx.api.state import AppState
from chatddx.api.test.helpers import bearer, endpoint
from chatddx.bench.handles import broken
from chatddx.catalog.titles import short
from chatddx.factors.engine import model_of
from chatddx.identity import Person
from chatddx.inventory import EndpointSpec, Inventory
from chatddx.store import Catalog, Rows, Store
from chatddx.store.store import Connection
from chatddx.test.helpers import ZERO
from chatddx.test.world import (
    GPT_OSS,
    GPT_OSS_ARTIFACT,
    LINES,
    MISTRAL,
    MISTRAL_ARTIFACT,
    QWEN,
    QWEN_ARTIFACT,
    QWEN_BARE,
    QWEN_BARE_ARTIFACT,
    QWEN_MODEL,
    REMOTE,
    TEST,
    UNKNOWN_MODEL,
)

NOTED = {
    "diagnosis": {"pattern": "sepsis | septic & shock"},
    "notes": [
        {"author": "carol", "comment": "Chock."},
        {"author": "dave", "comment": "Uteslut UVI."},
    ],
}


@pytest.mark.slow
def test_endpoints_say_what_they_serve_and_what_they_re_cleared_for(
    signed: TestClient,
) -> None:
    inventory = Inventory.load(TEST / "inventory.toml")
    listed = signed.get("/api/endpoints").json()
    assert [e["name"] for e in listed] == sorted(inventory.endpoints)
    for shown in listed:
        name = shown["name"]
        spec = inventory.endpoint(name)
        assert (shown["engine"], shown["host"], shown["capacity"]) == (
            spec.engine,
            spec.host,
            spec.capacity,
        )
        assert (shown["credential"], shown["cleared_for"], shown["problem"]) == (
            spec.credential,
            sorted(inventory.cleared.get(name, ())),
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
    model = signed.get(f"/api/components/{engine['model']}").json()["body"]
    assert (remote["serves"], remote["model"], remote["url"], remote["host"]) == (
        engine["model"],
        model["name"],
        str(inventory.endpoint(REMOTE).url),
        None,
    )
    assert remote["credential"] is not None and remote["cleared_for"] == []
    typed = {e["name"] for e in listed if e["takes_typed"]}
    assert typed == {n for n in endpoints if "typed" in inventory.cleared.get(n, ())}
    assert QWEN in typed and REMOTE not in typed


def test_an_endpoint_whose_engine_isn_t_stored_says_so(
    served: FastAPI, signed: TestClient
) -> None:
    held = served.state.chatddx
    ghost = EndpointSpec(engine=ZERO, url=HttpUrl("http://127.0.0.1:1/v1/"))
    endpoints = {**held.inventory.endpoints, "ghost@nowhere": ghost}
    served.state.chatddx = AppState(
        held.conninfo,
        held.inventory.model_copy(update={"endpoints": endpoints}),
        held.listener,
    )
    shown = endpoint(signed, "ghost@nowhere")
    assert (shown["title"], shown["model"], shown["url"]) == (
        None,
        None,
        "http://127.0.0.1:1/v1/",
    )
    assert "isn't in the store" in shown["problem"]


def test_models_are_their_handles_each_with_its_latest_engine_and_facts(
    signed: TestClient,
) -> None:
    models = {m["name"]: m for m in signed.get("/api/models").json()}
    endpoints = {e["name"]: e for e in signed.get("/api/endpoints").json()}
    for handle, at in (
        (QWEN_ARTIFACT, QWEN),
        (QWEN_BARE_ARTIFACT, QWEN_BARE),
        (GPT_OSS_ARTIFACT, GPT_OSS),
        (MISTRAL_ARTIFACT, MISTRAL),
        (UNKNOWN_MODEL, REMOTE),
    ):
        held, served = models.pop(handle), endpoints[at]
        assert (held["weights"], held["engine"]) == (served["serves"], served["engine"])
        assert held["takes_typed"] == served["takes_typed"]
        assert (held["facts"] is None) == (handle == UNKNOWN_MODEL)
    assert models == {}


def test_a_model_no_endpoint_here_serves_is_none_to_run_under(
    served: FastAPI, signed: TestClient
) -> None:
    held = served.state.chatddx
    endpoints = {n: e for n, e in held.inventory.endpoints.items() if n != QWEN}
    served.state.chatddx = AppState(
        held.conninfo,
        held.inventory.model_copy(update={"endpoints": endpoints}),
        held.listener,
    )
    assert QWEN_ARTIFACT not in {m["name"] for m in signed.get("/api/models").json()}


def test_a_world_broken_under_a_running_app_is_answered_raw(
    served: FastAPI, conn: Connection, alice: Person
) -> None:
    inventory = served.state.chatddx.inventory
    weights = model_of(inventory.endpoint(QWEN).engine, Store(conn).get).digest
    _ = Catalog(conn).create(weights, alice.id, name="twin")
    assert broken(Rows(conn), inventory) == [
        f"model threads {QWEN_ARTIFACT}, twin hold weights {short(weights)}, which one "
        + "model thread should"
    ]
    with TestClient(
        served, base_url="https://testserver", raise_server_exceptions=False
    ) as raw:
        raw.headers.update(bearer(conn, alice))
        query = {"kind": "configuration", "name": LINES, "owner": "alice"}
        [lines] = raw.get("/api/threads", params=query).json()
        got = raw.get(f"/api/threads/{lines['id']}/variation")
    assert (got.status_code, got.json()) == (
        500,
        {
            "code": "error",
            "detail": f"RuntimeError: {short(weights)} is held by 2 model threads, "
            + "not one: fix boot-check src/chatddx/bench/handles.py:broken",
        },
    )


@pytest.mark.slow
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
    got = signed.get(f"/api/components/{ZERO}")
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no component {ZERO} in the store", "code": "not_found"},
    )


def test_selectors_pick_from_a_document_or_say_why_they_don_t_read(
    signed: TestClient,
) -> None:
    selectors = [
        "/diagnosis",
        "$.notes[?@.author == 'carol'].comment",
        "$.notes[*].author",
        "/warning",
        "",
        "$.notes[",
    ]
    got = signed.post("/api/picks", json={"document": NOTED, "selectors": selectors})
    assert got.status_code == 200
    *read, broken = got.json()
    assert [p["items"] for p in read] == [
        [NOTED["diagnosis"]],
        ["Chock."],
        ["carol", "dave"],
        [],
        [NOTED],
    ]
    assert all(p["problem"] is None for p in read)
    assert broken["items"] is None and broken["problem"]
