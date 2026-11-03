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


def test_a_preview_is_the_request_drafted_as_far_as_it_is_translated(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES_GUIDED)
    parts = recipe(signed, mine)
    instructions = held(signed, parts["instructions"])
    old, *rest = instructions["text"]
    new = old.replace("Read the case", "Read the case closely")
    edited = {**instructions, "text": [new, *rest]}
    into = held(signed, parts["translations"])["into"]
    previews = f"/api/threads/{mine['id']}/previews"

    got = signed.post(previews, json={"chunks": {"instructions": edited}})
    assert got.status_code == 200, got.json()
    shown = got.json()
    system, *_, user = shown["messages"]
    assert system["runs"][0] == {
        "text": new,
        "origin": "instructions",
        "untranslated": False,
        "slot": None,
        "appendix": None,
    }
    assert [r["appendix"] for r in user["runs"] if r["appendix"]] == [1, 2]
    assert {"slot": "vignette"}.items() <= next(
        r for r in user["runs"] if r["slot"]
    ).items()
    sent = shown["request"]["messages"]
    assert sent[0]["content"].startswith(new)
    assert "‹appendix 1›" in sent[-1]["content"] and "seed" not in shown["request"]

    swedish = signed.post(
        previews,
        json={
            "chunks": {"instructions": edited},
            "translations": into,
            "language": "sv",
        },
    ).json()
    first = swedish["messages"][0]["runs"][0]
    assert (first["text"], first["untranslated"]) == (new, True)
    kept = signed.post(previews, json={"translations": into, "language": "sv"}).json()
    first = kept["messages"][0]["runs"][0]
    assert (first["text"], first["untranslated"]) == (into["sv"][old], False)
    saved = signed.post(previews, json={"language": "sv"}).json()
    assert saved["messages"] == kept["messages"]
    bare = signed.post(previews, json={"translations": {}, "language": "sv"}).json()
    assert bare["messages"][0]["runs"][0]["untranslated"]


@pytest.mark.slow
def test_a_configuration_saved_independent_is_forked_from_nothing(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    parts = recipe(signed, mine)
    changed = {**held(signed, parts["sampling"]), "temperature": 0.42}
    saves = f"/api/threads/{mine['id']}/saves"
    given = {"head": mine["head"]["id"], "chunks": {"sampling": changed}}
    forked = signed.post(saves, json={**given, "name": "warmer"}).json()
    alone = signed.post(saves, json={**given, "name": "alone", "independent": True})
    assert alone.status_code == 201, alone.json()
    detail = signed.get(f"/api/threads/{alone.json()['id']}").json()
    assert detail["forked_from"] is None
    assert signed.get(f"/api/threads/{forked['id']}").json()["forked_from"] is not None
    named = holders(signed, "sampling", recipe(signed, alone.json())["sampling"])
    assert "alone sampling" in [s["name"] for s in named]
    nameless = signed.post(saves, json={**given, "independent": True})
    assert nameless.status_code == 422
