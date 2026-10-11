from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.bench import Bench
from chatddx.bench.test.sample import another_expectation
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.curation import load_cases
from chatddx.curation.plan import SAMPLE
from chatddx.store import Catalog

pytestmark = pytest.mark.wip


def dutchfall(signed: TestClient, name: str = "Dutchfall11w") -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": name}).json()
    return found


def dropped(signed: TestClient, bench: Bench, family: dict[str, Any]) -> dict[str, Any]:
    [held] = signed.get(f"/api/families/{family['id']}").json()["expectations"]
    catalog, person, case = Catalog(bench.conn), bench.person.id, family["case"]
    choices = catalog.expectation_choices([case], person, held["expectation_schema"])
    [mine] = choices[case]
    catalog.note(Subject(thread=mine), Entry(field=EntryField.DELETED), person)
    return held


def test_cases_are_listed_with_their_tags_and_language(signed: TestClient) -> None:
    listed = signed.get("/api/families").json()
    assert len(listed) == len(load_cases(SAMPLE))
    assert {f["language"] for f in listed} == {"en", "sv"}
    assert all(f["case"].startswith("sha256:") and f["tags"] for f in listed)

    tags = signed.get("/api/tags").json()
    assert tags == sorted({t for f in listed for t in f["tags"]})
    tagged = signed.get("/api/families", params={"tag": tags[0]}).json()
    assert tagged and all(tags[0] in f["tags"] for f in tagged)


@pytest.mark.slow
def test_a_case_is_shown_with_the_expectation_it_is_scored_against(
    signed: TestClient, bench: Bench
) -> None:
    found = dutchfall(signed)
    shown = signed.get(f"/api/families/{found['id']}").json()
    assert {k: shown[k] for k in found} == found
    [held] = shown["expectations"]
    assert held["title"] and held["expectation"].startswith("sha256:")
    assert held["data"] and held["ambiguous"] is None

    _ = another_expectation(bench, found["case"], {"diagnosis": {"pattern": "x"}})
    [held] = signed.get(f"/api/families/{found['id']}").json()["expectations"]
    assert (held["expectation"], held["data"]) == (None, None)
    assert "has expectations to choose from" in held["ambiguous"]


@pytest.mark.slow
def test_a_person_takes_the_expectations_shared_with_them_for_many_cases(
    signed: TestClient, bench: Bench
) -> None:
    eleven, ten = dutchfall(signed), dutchfall(signed, "DutchFall10w")
    held = dropped(signed, bench, eleven)
    [archives] = held["shared"]
    assert archives["owner"] == "archive"
    schema = held["expectation_schema"]
    body = {"families": [eleven["id"], ten["id"]], "expectation_schema": schema}

    got = signed.post("/api/takes", json=body)
    assert got.status_code == 200
    taken = got.json()
    [made] = taken["taken"].values()
    assert list(taken["taken"]) == [str(eleven["id"])]
    assert list(taken["kept"]) == [str(ten["id"])]
    assert (taken["choosing"], taken["missing"]) == ({}, [])
    shown = signed.get(f"/api/threads/{made}").json()
    assert (shown["owner"], shown["forked_from"]) == ("alice", archives["head"]["id"])
    [held] = signed.get(f"/api/families/{eleven['id']}").json()["expectations"]
    assert held["expectation"] == archives["head"]["digest"]

    again = signed.post("/api/takes", json={**body, "owner": "archive"}).json()
    assert again["taken"] == {} and len(again["kept"]) == 2

    for wrong, said in (
        ({**body, "families": [eleven["id"], 0]}, "no case 0 for alice"),
        ({**body, "owner": "nobody"}, "no person 'nobody'"),
        ({**body, "expectation_schema": eleven["case"]}, "isn't a stored expectation"),
    ):
        got = signed.post("/api/takes", json=wrong)
        assert got.status_code == 422
        assert said in got.json()["detail"]
    assert signed.post("/api/takes", json={**body, "families": []}).status_code == 422


def test_a_case_s_vignette_is_fetched_from_its_source(signed: TestClient) -> None:
    found = dutchfall(signed)
    vignette = signed.get(f"/api/families/{found['id']}/vignette").json()
    assert (vignette["source"], vignette["drifted"]) == ("sample", False)
    assert vignette["text"].strip()


def test_a_case_the_person_doesn_t_see_isn_t_found(
    signed: TestClient, bob: dict[str, str]
) -> None:
    found = dutchfall(signed)
    for path in (
        f"/api/families/{found['id']}",
        f"/api/families/{found['id']}/vignette",
    ):
        got = signed.get(path, headers=bob)
        assert got.status_code == 404
        assert got.json() == {"detail": f"no case {found['id']} for bob"}
    assert signed.get("/api/families", headers=bob).json() == []
