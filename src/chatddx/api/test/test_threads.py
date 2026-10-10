from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.bench.test.sample import FREE_TEXT
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.identity import Person
from chatddx.store import Catalog
from chatddx.store.store import Connection

pytestmark = pytest.mark.wip


def configuration(signed: TestClient, owner: str) -> dict[str, Any]:
    query = {"kind": "configuration", "name": FREE_TEXT, "owner": owner}
    [found] = signed.get("/api/threads", params=query).json()
    return found


def test_threads_are_listed_by_kind_among_those_the_person_sees(
    signed: TestClient, conn: Connection, alice: Person
) -> None:
    listed = signed.get("/api/threads", params={"kind": "configuration"}).json()
    assert {t["owner"] for t in listed} == {"alice", "archive"}
    assert {t["kind"] for t in listed} == {"skeleton"}
    assert all(t["title"] and t["head"]["digest"].startswith("sha256:") for t in listed)
    named = signed.get(
        "/api/threads", params={"kind": "configuration", "name": FREE_TEXT}
    )
    assert sorted(t["owner"] for t in named.json()) == ["alice", "archive"]

    mine = configuration(signed, "alice")
    Catalog(conn).note(
        Subject(thread=mine["id"]), Entry(field=EntryField.TAG, value="keep"), alice.id
    )
    kept = signed.get("/api/threads", params={"kind": "configuration", "tag": "keep"})
    assert [t["id"] for t in kept.json()] == [mine["id"]]

    engines = signed.get("/api/threads", params={"kind": "engine"}).json()
    assert engines and {t["kind"] for t in engines} <= {"engine.local", "engine.remote"}
    nope = signed.get("/api/threads", params={"kind": "stack"})
    assert nope.status_code == 422 and nope.json()["detail"].startswith(
        "no kind 'stack'"
    )


def test_a_thread_is_shown_with_its_recipe_and_its_versions(signed: TestClient) -> None:
    mine, archives = configuration(signed, "alice"), configuration(signed, "archive")

    shown = signed.get(f"/api/threads/{mine['id']}").json()
    assert {k: shown[k] for k in mine} == mine
    assert shown["forked_from"] == archives["head"]["id"]
    assert shown["recipe"]["prompt"].startswith("sha256:")
    assert shown["recipe"]["toolset"] is None
    assert shown["collaborators"] == []

    edits = signed.get(f"/api/threads/{mine['id']}/edits").json()
    assert edits[-1] == mine["head"]


def test_a_thread_the_person_doesn_t_see_isn_t_found(
    signed: TestClient, bob: dict[str, str]
) -> None:
    mine = configuration(signed, "alice")
    for path in (f"/api/threads/{mine['id']}", f"/api/threads/{mine['id']}/edits"):
        got = signed.get(path, headers=bob)
        assert got.status_code == 404
        assert got.json() == {"detail": f"no thread {mine['id']} for bob"}
    assert (
        signed.get("/api/threads", params={"kind": "configuration"}, headers=bob).json()
        == []
    )
