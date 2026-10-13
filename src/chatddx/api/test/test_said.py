import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.test_variations import thread
from chatddx.test.world import LINES

pytestmark = pytest.mark.solidified


def test_an_owner_says_what_a_thread_is_called_and_who_it_is_shared_with(
    signed: TestClient, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    path = f"/api/threads/{mine['id']}"
    assert signed.get(path, headers=bob).status_code == 404

    asked = {
        "name": "terse",
        "description": "Short answers.",
        "tags": ["short", "ddx"],
        "collaborators": ["bob"],
    }
    got = signed.patch(path, json=asked)
    assert got.status_code == 200
    said = got.json()
    assert (said["name"], said["description"], said["deleted"]) == (
        "terse",
        "Short answers.",
        False,
    )
    assert (said["tags"], said["collaborators"]) == (["ddx", "short"], ["bob"])
    assert signed.get(path, headers=bob).json()["name"] == "terse"

    cleared = signed.patch(path, json={"name": None, "collaborators": []}).json()
    assert cleared["name"] is None and cleared["title"]
    assert (cleared["tags"], cleared["collaborators"]) == (["ddx", "short"], [])
    assert signed.get(path, headers=bob).status_code == 404


def test_what_isn_t_the_owner_s_to_say_is_refused(signed: TestClient) -> None:
    mine = thread(signed, "configuration", LINES)
    archives = thread(signed, "configuration", LINES, "archive")
    path = f"/api/threads/{mine['id']}"
    for asked, status, said in (
        ({"description": None}, 422, "a description is replaced, never taken away"),
        ({"collaborators": ["nobody"]}, 422, "no person 'nobody'"),
        ({"name": ""}, 422, "a name can't be empty"),
        ({"collaborators": ["alice"]}, 422, "is yours"),
    ):
        got = signed.patch(path, json=asked)
        assert got.status_code == status, (asked, got.json())
        assert said in got.json()["detail"]
    got = signed.patch(f"/api/threads/{archives['id']}", json={"name": "mine"})
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no configuration {archives['id']} of yours"},
    )
    assert signed.get(path).json()["name"] == mine["name"]


@pytest.mark.slow
def test_an_owner_deletes_and_restores_a_thread(
    signed: TestClient, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    path = f"/api/threads/{mine['id']}"
    listed = {"kind": "configuration"}
    _ = signed.patch(path, json={"collaborators": ["bob"]})

    assert signed.delete(path).status_code == 204
    assert signed.delete(path).status_code == 204
    assert signed.get(path).json()["deleted"] is True
    assert signed.get(f"{path}/edits").status_code == 200
    assert signed.get(path, headers=bob).status_code == 404
    live = [t["id"] for t in signed.get("/api/threads", params=listed).json()]
    gone = signed.get("/api/threads", params={**listed, "deleted": True}).json()
    assert mine["id"] not in live and [t["id"] for t in gone] == [mine["id"]]

    got = signed.patch(path, json={"name": "gone"})
    assert got.status_code == 422
    assert "is deleted: restore it to say more of it" in got.json()["detail"]
    back = signed.patch(path, json={"deleted": False, "name": "back"}).json()
    assert (back["deleted"], back["name"], back["collaborators"]) == (
        False,
        "back",
        ["bob"],
    )


def test_saying_needs_a_session(client: TestClient) -> None:
    assert client.patch("/api/threads/1", json={"name": "x"}).status_code == 401
    assert client.delete("/api/threads/1").status_code == 401
