import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.factors.engine import FileDigest, LocalModel
from chatddx.identity import Person
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.portal.test.test_varying import held, thread
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, OFF, QWEN_ARTIFACT, QWEN_MODEL


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def thread_props(page: str) -> dict[str, Any]:
    return held(page.replace('id="thread-props"', 'id="variation-props"'))


@pytest.mark.slow
def test_the_library_lists_each_kind_one_s_own_first(signed: TestClient) -> None:
    page = shown(signed, "/library?kind=reasoning")
    listed = signed.get("/api/threads", params={"kind": "reasoning"}).json()
    for t in listed:
        assert f'href="/threads/{t["id"]}"' in page
    mine = [t for t in listed if t["owner"] == "alice"]
    others = [t for t in listed if t["owner"] != "alice"]
    assert page.index(f'/threads/{mine[0]["id"]}"') < page.index(
        f'/threads/{others[0]["id"]}"'
    )
    assert 'href="/library?kind=appendix"' in page and "Library" in page
    got = signed.get("/library?kind=configuration")
    assert (got.status_code, got.headers["location"]) == (303, "/configurations")
    assert signed.get("/library?kind=stack").status_code == 404


@pytest.mark.slow
def test_a_thread_s_page_holds_its_versions_and_what_is_said(
    signed: TestClient,
) -> None:
    off = thread(signed, "reasoning", OFF)
    page = shown(signed, f"/threads/{off['id']}")
    assert "What is said of it" in page and "Fork it" in page
    given = thread_props(page)
    assert given["word"] == "reasoning"
    assert [v["digest"] for v in given["versions"]] == [off["head"]["digest"]]
    assert given["versions"][0]["body"]["kind"] == "chunk.reasoning"

    archives = thread(signed, "reasoning", OFF, "archive")
    page = shown(signed, f"/threads/{archives['id']}")
    assert "What is said of it" not in page and "Fork it" in page

    lines = thread(signed, "configuration", LINES)
    got = signed.get(f"/threads/{lines['id']}")
    assert (got.status_code, got.headers["location"]) == (
        303,
        f"/configurations/{lines['id']}",
    )


@pytest.mark.slow
def test_a_chunk_s_page_edits_it_in_a_form_of_its_kind(signed: TestClient) -> None:
    off = thread(signed, "reasoning", OFF)
    editor = thread_props(shown(signed, f"/threads/{off['id']}"))["editor"]
    body = signed.get(f"/api/components/{off['head']['digest']}").json()["body"]
    assert editor == {
        "mode": "edit",
        "thread": off["id"],
        "head": off["head"]["id"],
        "name": OFF,
        "kind": "chunk",
        "chunk": "chunk.reasoning",
        "languaged": False,
        "tools": [],
        "me": "alice",
        "body": body,
        "language": None,
    }
    archives = thread(signed, "reasoning", OFF, "archive")
    page = shown(signed, f"/threads/{archives['id']}")
    assert thread_props(page)["editor"]["mode"] == "fork"

    lines = thread(signed, "output", LINES)
    given = thread_props(shown(signed, f"/threads/{lines['id']}"))["editor"]
    assert given["languaged"]
    assert given["language"] == lines["language"] == "en"
    toolset = signed.get(
        "/api/threads", params={"kind": "toolset", "owner": "alice"}
    ).json()[0]
    tools = thread_props(shown(signed, f"/threads/{toolset['id']}"))["editor"]["tools"]
    assert tools == signed.get("/api/threads", params={"kind": "tool"}).json()


@pytest.mark.slow
def test_a_chunk_is_begun_from_the_library(signed: TestClient) -> None:
    assert 'href="/library/new?kind=prompt"' in shown(signed, "/library?kind=prompt")
    for kind in ("appendix", "translations", "tool"):
        assert "/library/new" not in shown(signed, f"/library?kind={kind}")
    page = shown(signed, "/library/new?kind=sampling")
    editor = json.loads(
        page.split("data-chunk-editor>", 1)[1]
        .split('<script type="application/json">', 1)[1]
        .split("</script>", 1)[0]
    )
    assert editor == {
        "mode": "new",
        "name": "",
        "body": None,
        "language": None,
        "kind": "chunk",
        "chunk": "chunk.sampling",
        "languaged": False,
        "tools": [],
        "me": "alice",
    }
    for kind in ("translations", "tool", "stack"):
        assert signed.get(f"/library/new?kind={kind}").status_code == 404


@pytest.mark.slow
def test_a_judge_s_page_edits_its_configuration_handle_and_seeds(
    signed: TestClient, conn: Connection, alice: Person
) -> None:
    verdict = thread(signed, "judge", "verdict", "archive")
    page = f"/threads/{verdict['id']}"
    editor = thread_props(shown(signed, page))["editor"]
    body = signed.get(f"/api/components/{verdict['head']['digest']}").json()["body"]
    models = {m["name"]: m["weights"] for m in signed.get("/api/models").json()}
    query = {"kind": "configuration", "purpose": "judge"}
    judging = signed.get("/api/threads", params=query).json()
    held = ("mode", "kind", "body", "handle", "behind", "problem", "me")
    assert {k: editor[k] for k in held} == {
        "mode": "fork",
        "kind": "judge",
        "body": body,
        "handle": QWEN_ARTIFACT,
        "behind": False,
        "problem": None,
        "me": "alice",
    }
    assert body["model"] == models[QWEN_ARTIFACT]
    assert {"name": QWEN_ARTIFACT, "weights": models[QWEN_ARTIFACT]} in editor["models"]
    assert {j["thread"] for j in editor["judging"]} == {t["id"] for t in judging}

    mine = {**body, "seeds": [4]}
    made = signed.post("/api/threads", json={"component": mine, "name": "mine"})
    assert made.status_code == 201
    assert thread_props(shown(signed, f"/threads/{made.json()['id']}"))["editor"][
        "mode"
    ] == ("edit")

    store = Store(conn)
    registry = store.load([])
    weights = registry.add(
        LocalModel(
            repo=QWEN_MODEL,
            revision="newer",
            files=(FileDigest(path="none", sha256="0" * 64),),
        )
    )
    _ = store.add(registry, [weights])
    handle = thread(signed, "model", QWEN_ARTIFACT, "archive")
    _ = Catalog(conn).edit(handle["id"], weights, alice.id)
    behind = thread_props(shown(signed, page))["editor"]
    assert (behind["handle"], behind["behind"]) == (QWEN_ARTIFACT, True)
    assert behind["problem"] == (
        f"no endpoint serves model {QWEN_ARTIFACT}, which is ops' to mend"
    )


@pytest.mark.slow
def test_a_judge_is_begun_from_the_library(signed: TestClient) -> None:
    assert 'href="/library/new?kind=judge"' in shown(signed, "/library?kind=judge")
    page = shown(signed, "/library/new?kind=judge")
    editor = json.loads(
        page.split("data-judge-editor>", 1)[1]
        .split('<script type="application/json">', 1)[1]
        .split("</script>", 1)[0]
    )
    held = ("mode", "name", "kind", "body", "handle", "problem")
    assert {k: editor[k] for k in held} == {
        "mode": "new",
        "name": "",
        "kind": "judge",
        "body": None,
        "handle": None,
        "problem": None,
    }
    assert editor["judging"] and editor["models"]


@pytest.mark.slow
def test_a_configuration_is_made_from_a_recipe_of_the_chunks_one_sees(
    signed: TestClient,
) -> None:
    page = shown(signed, "/configurations")
    opened = '<script type="application/json" id="recipe-props">'
    given = json.loads(page.split(opened, 1)[1].split("</script>", 1)[0])
    assert (given["purpose"], given["me"]) == ("generation", "alice")
    assert "prompt" not in given["optional"] and "reasoning" in given["optional"]
    reasoning = signed.get("/api/threads", params={"kind": "reasoning"}).json()
    assert [t["id"] for t in given["choices"]["reasoning"]] == [
        t["id"] for t in reasoning
    ]
    assert QWEN_ARTIFACT in {t["name"] for t in given["choices"]["model"]}
    judged = shown(signed, "/configurations?purpose=judge")
    assert '"purpose": "judge"' in judged


@pytest.mark.slow
def test_what_is_said_of_a_thread_is_changed_and_it_is_deleted_and_restored(
    signed: TestClient,
) -> None:
    off = thread(signed, "reasoning", OFF)
    path = f"/threads/{off['id']}"
    form = {
        "name": "quiet",
        "description": "No thinking.",
        "tags": "b, a",
        "shared": "",
    }
    got = signed.post(f"{path}/said", data=form)
    assert (got.status_code, got.headers["location"]) == (303, path)
    said = signed.get(f"/api/threads/{off['id']}").json()
    assert (said["name"], said["description"], said["tags"]) == (
        "quiet",
        "No thinking.",
        ["a", "b"],
    )

    got = signed.post(f"{path}/said", data={**form, "shared": "nobody-at-all"})
    assert got.status_code == 422 and "no person" in got.text

    assert signed.post(f"{path}/delete").status_code == 303
    page = shown(signed, path)
    assert "You deleted it" in page and "What is said of it" not in page
    assert f'action="{path}/restore"' in shown(signed, "/library")
    assert signed.post(f"{path}/restore").status_code == 303
    assert "You deleted it" not in shown(signed, path)


@pytest.mark.slow
def test_a_fork_follows_its_origin_once_that_moves_on(signed: TestClient) -> None:
    off = thread(signed, "reasoning", OFF)
    got = signed.post(f"/threads/{off['id']}/fork", data={"name": "mine too"})
    assert got.status_code == 303
    fork = int(got.headers["location"].removeprefix("/threads/"))
    page = shown(signed, f"/threads/{fork}")
    assert f'href="/threads/{off["id"]}">a fork' in page
    assert "Its origin has moved on" not in page

    body = signed.get(f"/api/components/{off['head']['digest']}").json()["body"]
    edits = f"/api/threads/{off['id']}/edits"
    moved = {**body, "thinking_token_budget": 64}
    got = signed.post(edits, json={"head": off["head"]["id"], "component": moved})
    assert got.status_code == 201
    page = shown(signed, f"/threads/{fork}")
    assert "Its origin has moved on" in page
    head = signed.get(f"/api/threads/{fork}").json()["head"]
    assert (
        signed.post(f"/threads/{fork}/follow", data={"head": head["id"]}).status_code
        == 303
    )
    assert "Its origin has moved on" not in shown(signed, f"/threads/{fork}")
    assert len(thread_props(shown(signed, f"/threads/{fork}"))["versions"]) == 2


@pytest.mark.slow
def test_a_thread_s_forms_from_another_site_write_nothing(signed: TestClient) -> None:
    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    actions = ("said", "delete", "restore", "fork", "follow", "moved/follow", "take")
    for action in (*actions, "carry"):
        assert signed.post(f"/threads/1/{action}", headers=elsewhere).status_code == 403
