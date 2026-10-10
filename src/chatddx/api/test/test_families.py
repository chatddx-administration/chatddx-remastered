from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.bench import Bench
from chatddx.bench.test.sample import another_expectation
from chatddx.curation import load_cases
from chatddx.curation.plan import SAMPLE

pytestmark = pytest.mark.wip


def dutchfall(signed: TestClient) -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": "Dutchfall11w"}).json()
    return found


def test_cases_are_listed_with_their_tags_and_language(signed: TestClient) -> None:
    listed = signed.get("/api/families").json()
    assert len(listed) == len(load_cases(SAMPLE))
    assert {f["language"] for f in listed} == {"en", "sv"}
    assert all(f["case"].startswith("sha256:") and f["tags"] for f in listed)

    tags = signed.get("/api/tags").json()
    assert tags == sorted({t for f in listed for t in f["tags"]})
    tagged = signed.get("/api/families", params={"tag": tags[0]}).json()
    assert tagged and all(tags[0] in f["tags"] for f in tagged)


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
