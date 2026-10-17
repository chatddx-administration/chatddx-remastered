import json
from typing import Any
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from chatddx.identity import Person
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in


@pytest.fixture
def template(ran: str) -> str:
    return ran


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def family(signed: TestClient, name: str) -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": name}).json()
    return found


def props(page: str) -> dict[str, Any]:
    held = page.split('<script type="application/json" id="review-props">', 1)[1]
    return json.loads(held.split("</script>", 1)[0])


@pytest.mark.slow
def test_review_opens_the_first_case_of_the_list_and_keeps_its_tag(
    signed: TestClient,
) -> None:
    [first, *_] = signed.get("/api/families").json()
    got = signed.get("/review")
    assert (got.status_code, got.headers["location"]) == (303, f"/review/{first['id']}")
    [swedish, *_] = signed.get("/api/families", params={"tag": "swedish"}).json()
    got = signed.get("/review", params={"tag": "swedish"})
    assert got.headers["location"] == f"/review/{swedish['id']}?tag=swedish"
    page = shown(signed, "/review?tag=nothing-tagged-so")
    assert "No case to review tagged nothing-tagged-so." in page


@pytest.mark.slow
def test_a_case_is_reviewed_with_what_is_expected_and_what_each_view_reads_of_it(
    signed: TestClient,
) -> None:
    noted = family(signed, "noted")
    page = shown(signed, f"/review/{noted['id']}")
    vignette = signed.get(f"/api/families/{noted['id']}/vignette").json()["text"]
    assert escape(vignette.strip().splitlines()[0]) not in page
    assert f'href="/families/{noted["id"]}/vignette"' in page

    [case] = signed.get(f"/api/families/{noted['id']}").json()["cases"]
    [expected] = case["expectations"]
    for note in expected["data"]["notes"]:
        assert escape(note["comment"]) in page

    scorers = signed.get("/api/threads", params={"kind": "scorer"}).json()
    judged = next(t for t in scorers if t["name"] == "judged")
    page = shown(signed, f"/review/{noted['id']}?scorer={judged['id']}")
    held = signed.get(f"/api/components/{judged['head']['digest']}").json()["body"]
    selectors = [v["expectation"] for v in held["views"]]
    picks = signed.post(
        "/api/picks", json={"document": expected["data"], "selectors": selectors}
    ).json()
    carol = next(p for p, s in zip(picks, selectors, strict=True) if "carol" in s)
    assert carol["items"] and all(escape(i) in page for i in carol["items"])
    for s in selectors:
        assert escape(s) in page


@pytest.mark.slow
def test_the_answers_to_a_case_are_listed_with_each_view_s_value_and_nothing_sensitive(
    signed: TestClient,
) -> None:
    noted = family(signed, "noted")
    scorers = signed.get("/api/threads", params={"kind": "scorer"}).json()
    judged = next(t for t in scorers if t["name"] == "judged")
    page = shown(signed, f"/review/{noted['id']}")
    assert f'scorer={judged["id"]}" aria-current="page"' in page
    runs = signed.get("/api/runs", params={"reaching": noted["case"]}).json()
    assert runs
    given = props(page)
    assert {a["run"] for a in given["answers"]} == {r["id"] for r in runs}
    for r in runs:
        assert escape(r["described"]) in page
        [graded] = [
            g
            for g in signed.get(f"/api/runs/{r['id']}/scores").json()
            if g["scorer"] == judged["head"]["digest"]
        ]
        [answer] = [a for a in given["answers"] if a["run"] == r["id"]]
        assert answer["score"] == graded["score"]
        for item in graded["items"]:
            if item["case"] == noted["case"] and item["value"] is not None:
                assert f">{item['value']:.2f}</span>" in page
        for item in signed.get(f"/api/runs/{r['id']}/items").json():
            if isinstance(item["answer"]["value"], str):
                assert escape(item["answer"]["value"]) not in page
    assert given["labels"] and all(escape(lbl) in page for lbl in given["labels"])


@pytest.mark.slow
def test_a_family_s_other_case_shows_its_appendices(signed: TestClient) -> None:
    whitespace = family(signed, "whitespace")
    cases = signed.get(f"/api/families/{whitespace['id']}").json()["cases"]
    labs = next(c for c in cases if c["appendices"])
    page = shown(signed, f"/review/{whitespace['id']}")
    assert "None in this case." in page
    assert urlencode({"case": labs["case"]}) in page
    page = shown(signed, f"/review/{whitespace['id']}?case={labs['case']}")
    assert "CRP 180 mg/L, leukocytes 16." in page
    assert props(page)["case"] == labs["case"]


@pytest.mark.slow
def test_the_list_steps_to_the_case_before_and_after_with_what_is_picked(
    signed: TestClient,
) -> None:
    listed = signed.get("/api/families", params={"tag": "targets"}).json()
    assert len(listed) >= 3
    first, second, third = listed[:3]
    page = shown(signed, f"/review/{second['id']}?tag=targets")
    given = props(page)
    assert given["previous"] == f"/review/{first['id']}?tag=targets"
    assert given["next"] == f"/review/{third['id']}?tag=targets"
    assert (
        props(shown(signed, f"/review/{first['id']}?tag=targets"))["previous"] is None
    )
    for f in listed:
        assert f'href="/review/{f["id"]}?tag=targets"' in page


@pytest.mark.slow
def test_what_review_can_t_find_is_not_found(signed: TestClient) -> None:
    noted = family(signed, "noted")
    for query in ("case=sha256:nothing", "schema=sha256:nothing", "scorer=0"):
        got = signed.get(f"/review/{noted['id']}?{query}")
        assert got.status_code == 404, query
        assert got.headers["content-type"].startswith("text/html")
    assert signed.get("/review/0").status_code == 404
