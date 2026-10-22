from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.helpers import family
from chatddx.bench import Bench
from chatddx.bench.test.helpers import another_expectation, owned
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.curation import load_cases
from chatddx.store import Catalog
from chatddx.test.helpers import TYPED
from chatddx.test.world import DATA


def dropped(signed: TestClient, bench: Bench, family: dict[str, Any]) -> dict[str, Any]:
    [held] = signed.get(f"/api/families/{family['id']}").json()["cases"][0][
        "expectations"
    ]
    catalog, person, case = Catalog(bench.conn), bench.person.id, family["case"]
    [mine] = owned(bench, case, held["expectation_schema"])
    catalog.note(Subject(thread=mine), Entry(field=EntryField.DELETED), person)
    return held


def test_cases_are_listed_with_their_tags_and_language(signed: TestClient) -> None:
    listed = signed.get("/api/families").json()
    cases = load_cases(DATA)
    assert len(listed) == len(cases)
    assert {f["name"]: f["language"] for f in listed} == {
        id: case.language for id, case in cases.items()
    }
    assert {f["language"] for f in listed} == {"en", "sv"}
    assert {f["name"]: f["tags"] for f in listed} == {
        id: sorted(case.tags) for id, case in cases.items()
    }
    assert all(f["case"].startswith("sha256:") and f["tags"] for f in listed)

    tags = sorted({t for f in listed for t in f["tags"]})
    tagged = signed.get("/api/families", params={"tag": tags[0]}).json()
    assert tagged and all(tags[0] in f["tags"] for f in tagged)


@pytest.mark.slow
def test_a_case_is_shown_with_the_expectation_it_is_scored_against(
    signed: TestClient, bench: Bench
) -> None:
    found = family(signed)
    shown = signed.get(f"/api/families/{found['id']}").json()
    assert {k: shown[k] for k in found} == found
    [default] = shown["cases"]
    assert (default["case"], default["default"]) == (found["case"], True)
    [held] = default["expectations"]
    assert held["title"] and held["expectation"].startswith("sha256:")
    assert held["data"] and held["ambiguous"] is None

    _ = another_expectation(bench, found["case"], {"diagnosis": {"pattern": "x"}})
    [held] = signed.get(f"/api/families/{found['id']}").json()["cases"][0][
        "expectations"
    ]
    assert (held["expectation"], held["data"]) == (None, None)
    assert "has expectations to choose from" in held["ambiguous"]


@pytest.mark.slow
def test_a_person_takes_the_expectations_shared_with_them_for_many_cases(
    signed: TestClient, bench: Bench
) -> None:
    crlf, bom = family(signed), family(signed, "bom")
    held = dropped(signed, bench, crlf)
    [archives] = held["shared"]
    assert archives["owner"] == "archive"
    schema = held["expectation_schema"]
    body = {"families": [crlf["id"], bom["id"]], "expectation_schema": schema}

    got = signed.post("/api/takes", json=body)
    assert got.status_code == 200
    taken = got.json()
    [made] = taken["taken"].values()
    assert list(taken["taken"]) == [str(crlf["id"])]
    assert list(taken["kept"]) == [str(bom["id"])]
    assert (taken["choosing"], taken["missing"]) == ({}, [])
    shown = signed.get(f"/api/threads/{made}").json()
    assert (shown["owner"], shown["forked_from"]) == ("alice", archives["head"]["id"])
    [held] = signed.get(f"/api/families/{crlf['id']}").json()["cases"][0][
        "expectations"
    ]
    assert held["expectation"] == archives["head"]["digest"]

    again = signed.post("/api/takes", json={**body, "owner": "archive"}).json()
    assert again["taken"] == {} and len(again["kept"]) == 2

    for wrong, said in (
        ({**body, "families": [crlf["id"], 0]}, "no case 0 for alice"),
        ({**body, "owner": "nobody"}, "no person 'nobody'"),
        ({**body, "expectation_schema": crlf["case"]}, "isn't a stored expectation"),
    ):
        got = signed.post("/api/takes", json=wrong)
        assert got.status_code == 422
        assert said in got.json()["detail"]
    assert signed.post("/api/takes", json={**body, "families": []}).status_code == 422


def test_a_case_s_vignette_is_fetched_from_its_source(signed: TestClient) -> None:
    found = family(signed)
    vignette = signed.get(f"/api/families/{found['id']}/vignette").json()
    assert (vignette["source"], vignette["drifted"]) == ("test", False)
    assert vignette["text"].strip()


def test_a_case_the_person_doesn_t_see_isn_t_found(
    signed: TestClient, bob: dict[str, str]
) -> None:
    found = family(signed)
    for path in (
        f"/api/families/{found['id']}",
        f"/api/families/{found['id']}/vignette",
    ):
        got = signed.get(path, headers=bob)
        assert got.status_code == 404
        assert got.json() == {
            "detail": f"no case {found['id']} for bob",
            "code": "not_found",
        }
    assert signed.get("/api/families", headers=bob).json() == []


@pytest.mark.slow
def test_an_owner_says_what_a_typed_case_is_and_a_collaborator_leaves_it(
    signed: TestClient, bob: dict[str, str]
) -> None:
    typed = signed.post(
        "/api/families", json={"text": TYPED, "language": "en", "name": "flight"}
    ).json()
    path = f"/api/families/{typed['id']}"
    asked = {"name": "breathless", "tags": ["typed"], "collaborators": ["bob"]}
    said = signed.patch(path, json={**asked, "language": "sv"})
    assert said.status_code == 200
    held = said.json()
    assert (held["name"], held["tags"], held["collaborators"], held["language"]) == (
        "breathless",
        ["typed"],
        ["bob"],
        "sv",
    )
    assert signed.get(path, headers=bob).status_code == 200
    got = signed.post(f"{path}/leave", headers=bob)
    assert (got.status_code, got.content) == (204, b"")
    assert signed.get(path, headers=bob).status_code == 404

    assert signed.patch(path, json={"deleted": True}).json()["deleted"] is True
    assert typed["id"] not in [f["id"] for f in signed.get("/api/families").json()]
    gone = signed.get("/api/families", params={"deleted": True}).json()
    assert [f["id"] for f in gone] == [typed["id"]]
    got = signed.patch(path, json={"name": "gone"})
    assert got.status_code == 422 and "is deleted" in got.json()["detail"]

    shared = family(signed, "crlf")
    got = signed.patch(f"/api/families/{shared['id']}", json={"name": "mine"})
    assert (got.status_code, got.json()["detail"]) == (
        404,
        f"no case {shared['id']} of yours",
    )
