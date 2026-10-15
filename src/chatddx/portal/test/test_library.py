from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.identity import Person
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.portal.test.test_varying import held, thread
from chatddx.test.world import LINES, OFF


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
    actions = ("said", "delete", "restore", "fork", "follow", "facts/follow", "take")
    for action in (*actions, "carry"):
        assert signed.post(f"/threads/1/{action}", headers=elsewhere).status_code == 403
