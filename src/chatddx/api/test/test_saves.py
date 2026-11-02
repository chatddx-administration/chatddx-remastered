from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.helpers import body, thread
from chatddx.test.world import LINES, LINES_GUIDED


def recipe(signed: TestClient, configuration: dict[str, Any]) -> dict[str, Any]:
    return signed.get(f"/api/threads/{configuration['id']}").json()["recipe"]


def held(signed: TestClient, digest: str) -> dict[str, Any]:
    return signed.get(f"/api/components/{digest}").json()["body"]


def holders(signed: TestClient, kind: str, digest: str) -> list[dict[str, Any]]:
    found = signed.get("/api/threads", params={"kind": kind, "owner": "alice"}).json()
    return [t for t in found if t["head"]["digest"] == digest]


@pytest.mark.slow
def test_a_chunk_saved_with_a_configuration_is_a_version_of_its_own_thread(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    parts = recipe(signed, mine)
    [sampling] = holders(signed, "sampling", parts["sampling"])
    changed = {**held(signed, parts["sampling"]), "temperature": 0.42}
    got = signed.post(
        f"/api/threads/{mine['id']}/saves",
        json={"head": mine["head"]["id"], "chunks": {"sampling": changed}},
    )
    assert got.status_code == 201, got.json()
    assert got.json()["id"] == mine["id"]

    after = recipe(signed, mine)
    assert after["sampling"] != parts["sampling"] and after["prompt"] == parts["prompt"]
    [kept] = holders(signed, "sampling", after["sampling"])
    assert (kept["id"], kept["name"]) == (sampling["id"], sampling["name"])
    assert body(signed, kept)["temperature"] == 0.42

    again = signed.post(
        f"/api/threads/{mine['id']}/saves",
        json={"head": mine["head"]["id"], "chunks": {"sampling": changed}},
    )
    assert again.status_code == 409


@pytest.mark.slow
def test_a_fork_saved_with_its_chunks_forks_them_under_their_names(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    parts = recipe(signed, mine)
    [sampling] = holders(signed, "sampling", parts["sampling"])
    changed = {**held(signed, parts["sampling"]), "temperature": 0.42}
    got = signed.post(
        f"/api/threads/{mine['id']}/saves",
        json={
            "head": mine["head"]["id"],
            "name": "warmer",
            "chunks": {"sampling": changed},
        },
    )
    assert got.status_code == 201, got.json()
    fork = got.json()
    assert fork["id"] != mine["id"] and fork["name"] == "warmer"
    assert recipe(signed, mine)["sampling"] == parts["sampling"]
    [forked] = holders(signed, "sampling", recipe(signed, fork)["sampling"])
    assert forked["id"] != sampling["id"] and forked["name"] == sampling["name"]


@pytest.mark.slow
def test_translations_follow_the_texts_changed_in_place_when_saved(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES_GUIDED)
    parts = recipe(signed, mine)
    instructions = held(signed, parts["instructions"])
    old, *rest = instructions["text"]
    new = old.replace("Read the case", "Read the case closely")
    edited = {**instructions, "text": [new, *rest]}
    language = signed.get(f"/api/threads/{mine['id']}").json()["language"]

    drafts = f"/api/threads/{mine['id']}/drafts"
    into = held(signed, parts["translations"])["into"]
    got = signed.post(
        drafts, json={"after": {"instructions": edited}, "translations": into}
    )
    assert got.status_code == 200, got.json()
    drafted = got.json()
    assert new in drafted["texts"]["instructions"]
    assert drafted["translations"]["sv"][new] == into["sv"][old]
    assert old not in drafted["translations"]["sv"]

    saved = signed.post(
        f"/api/threads/{mine['id']}/saves",
        json={"head": mine["head"]["id"], "chunks": {"instructions": edited}},
    )
    assert saved.status_code == 201, saved.json()
    after = recipe(signed, mine)
    assert held(signed, after["translations"])["into"] == drafted["translations"]
    assert language is not None
    assert signed.get(f"/api/threads/{mine['id']}").json()["language"] == language
