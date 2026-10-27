import json
from typing import Any
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from chatddx.api.test.helpers import family
from chatddx.portal.test.helpers import ran_template, run_title, shown
from chatddx.test.world import (
    GPT_OSS_ARTIFACT,
    MISTRAL_ARTIFACT,
    QWEN_ARTIFACT,
    QWEN_BARE_ARTIFACT,
    UNKNOWN_MODEL,
)

__all__ = ["ran_template"]


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
    assert f'href="/cases/{noted["id"]}/vignette"' in page

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
        assert escape(run_title(r)) in page
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


@pytest.mark.slow
def test_the_expectation_is_edited_in_place_with_its_versions_and_what_reads_it(
    signed: TestClient,
) -> None:
    noted = family(signed, "noted")
    scorers = signed.get("/api/threads", params={"kind": "scorer"}).json()
    judged = next(t for t in scorers if t["name"] == "judged")
    given = props(shown(signed, f"/review/{noted['id']}?scorer={judged['id']}"))
    expected = given["expected"]
    editor = expected["editor"]
    [case] = signed.get(f"/api/families/{noted['id']}").json()["cases"]
    [held] = case["expectations"]
    assert (editor["mode"], editor["case"], editor["data"]) == (
        "edit",
        noted["case"],
        held["data"],
    )
    assert expected["digest"] == held["expectation"]
    assert expected["history"][-1]["digest"] == held["expectation"]
    body = signed.get(f"/api/components/{judged['head']['digest']}").json()["body"]
    assert [v["expectation"] for v in expected["views"]] == [
        v["expectation"] for v in body["views"]
    ]
    assert given["back"] == f"/review/{noted['id']}?scorer={judged['id']}"


@pytest.mark.slow
def test_an_island_is_given_its_json_in_the_order_it_is_stored(
    signed: TestClient,
) -> None:
    noted = family(signed, "noted")
    expected = props(shown(signed, f"/review/{noted['id']}"))["expected"]
    editor = expected["editor"]
    expectation = signed.get(f"/api/components/{expected['digest']}").json()
    schema = signed.get(f"/api/components/{editor['schema']}").json()
    assert json.dumps(editor["data"]) == json.dumps(expectation["body"]["data"])
    assert json.dumps(editor["json_schema"]) == json.dumps(
        schema["body"]["json_schema"]
    )


@pytest.mark.slow
def test_what_is_shared_to_take_is_shown_with_its_take(signed: TestClient) -> None:
    noted = family(signed, "noted")
    [expected] = signed.get(f"/api/families/{noted['id']}").json()["cases"][0][
        "expectations"
    ]
    query = {"kind": "expectation", "owner": "alice"}
    mine = next(
        t
        for t in signed.get("/api/threads", params=query).json()
        if t["head"]["digest"] == expected["expectation"]
    )
    page = shown(signed, f"/review/{noted['id']}")
    assert "data-offered" not in page
    assert signed.patch(f"/api/threads/{mine['id']}", json={"deleted": True}).is_success
    [shared] = signed.get(f"/api/families/{noted['id']}").json()["cases"][0][
        "expectations"
    ][0]["shared"]
    page = shown(signed, f"/review/{noted['id']}")
    offered = page.split(f'data-offered="{shared["id"]}"', 1)[1]
    offered = offered.split('id="review-expected"', 1)[0]
    assert f'action="/threads/{shared["id"]}/take"' in offered
    for note in expected["data"]["notes"]:
        assert escape(note["comment"]) in offered


@pytest.mark.slow
def test_an_appendix_written_in_review_is_added_to_the_case_it_is_written_in(
    signed: TestClient,
) -> None:
    crlf = family(signed, "crlf")
    back = f"/review/{crlf['id']}?tag=targets"

    def written(name: str, text: str, case: str, at: str) -> tuple[str, str]:
        got = signed.post(
            f"/review/{crlf['id']}/appendices",
            data={"name": name, "text": text, "case": case, "back": at},
        )
        assert got.status_code == 303
        query = {"kind": "appendix", "owner": "alice", "name": name}
        [made] = signed.get("/api/threads", params=query).json()
        return made["head"]["digest"], got.headers["location"]

    def built(*appendices: str) -> dict[str, Any]:
        cases = signed.get(f"/api/families/{crlf['id']}").json()["cases"]
        return next(c for c in cases if c["appendices"] == list(appendices))

    default = built()
    ultrasound, at = written(
        "ultrasound", "Gallstones on ultrasound.", default["case"], back
    )
    alone = built(ultrasound)
    assert at == f"{back}&{urlencode({'case': alone['case']})}"
    page = shown(signed, at)
    assert "Gallstones on ultrasound." in page
    assert "f.appendices" not in page and "owned by" not in page
    given = props(page)
    [appendix] = given["appendices"]
    assert appendix["digest"] == ultrasound
    assert appendix["editor"]["mode"] == "edit"
    editor = given["expected"]["editor"]
    assert (editor["mode"], editor["case"]) == ("new", alone["case"])
    assert editor["data"] == default["expectations"][0]["data"]

    labs, again = written("labs", "Bilirubin 40.", alone["case"], at)
    assert again == f"{back}&{urlencode({'case': built(ultrasound, labs)['case']})}"


@pytest.mark.slow
def test_the_record_says_each_view_s_mean_over_the_answers(signed: TestClient) -> None:
    noted = family(signed, "noted")
    scorers = signed.get("/api/threads", params={"kind": "scorer"}).json()
    judged = next(t for t in scorers if t["name"] == "judged")
    page = shown(signed, f"/review/{noted['id']}?scorer={judged['id']}")
    assert 'data-drawer="record"' in page and 'data-drawer="cases"' in page
    for label in props(page)["labels"]:
        assert f"<dt>{escape(label)}</dt>" in page
    assert "mean of 1" in page


@pytest.mark.slow
def test_a_scorer_is_offered_to_compose_as_it_is_stored_with_what_it_can_read(
    signed: TestClient,
) -> None:
    noted = family(signed, "noted")
    scorers = signed.get("/api/threads", params={"kind": "scorer"}).json()
    judged = next(t for t in scorers if t["name"] == "judged")
    given = props(shown(signed, f"/review/{noted['id']}?scorer={judged['id']}"))
    composing = given["expected"]["composing"]
    held = composing["scorer"]
    body = signed.get(f"/api/components/{judged['head']['digest']}").json()["body"]
    assert (held["thread"], held["head"], held["digest"]) == (
        judged["id"],
        judged["head"]["id"],
        judged["head"]["digest"],
    )
    assert held["body"] == body and held["labels"] == given["labels"]
    assert held["mode"] == ("edit" if judged["owner"] == "alice" else "fork")
    judged = {v["judge"] for v in body["views"] if v["judge"]}
    assert judged <= set(composing["titles"])
    judges = signed.get("/api/threads", params={"kind": "judge"}).json()
    assert {j["digest"] for j in composing["judges"]} == {
        j["head"]["digest"] for j in judges
    }
    verdict = next(j for j in composing["judges"] if j["name"] == "verdict")
    assert verdict["output_schema"]["title"] == "Verdict" and verdict["seeds"] == [1]
    assert not any("texts" in j for j in composing["judges"])
    query = {"kind": "configuration", "purpose": "judge"}
    judging = signed.get("/api/threads", params=query).json()
    assert {j["digest"] for j in composing["judging"]} == {
        j["head"]["digest"] for j in judging
    }
    assert {m["name"] for m in composing["models"]} == {
        QWEN_ARTIFACT,
        QWEN_BARE_ARTIFACT,
        GPT_OSS_ARTIFACT,
        MISTRAL_ARTIFACT,
        UNKNOWN_MODEL,
    }
    blank = composing["blank"]
    assert blank["expectation_schema"] == body["expectation_schema"]
    code = signed.get("/api/scorer-code").json()[0]
    assert (blank["entry_point"], blank["version"]) == (
        code["entry_point"],
        code["version"],
    )
    assert composing["metrics"] == code["metrics"]
    runs = signed.get("/api/runs", params={"reaching": noted["case"]}).json()
    assert composing["runs"] == [r["id"] for r in runs]
    assert composing["case"] == noted["case"]
    assert None in {o["title"] for o in composing["outputs"]}


@pytest.mark.slow
def test_a_refusal_s_page_leads_back_where_the_form_was_and_nowhere_else(
    signed: TestClient,
) -> None:
    crlf = family(signed, "crlf")
    back = f"/review/{crlf['id']}?tag=targets"
    form = {"configuration": "0", "case": "sha256:" + "0" * 64}
    here = {"Referer": f"https://testserver{back}"}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form, headers=here)
    assert got.status_code == 422
    assert f'href="{escape(back)}"' in got.text and "Back to where you were" in got.text
    elsewhere = {"Referer": f"https://elsewhere.example{back}"}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form, headers=elsewhere)
    assert got.status_code == 422 and "Back to where you were" not in got.text
    gone = signed.get("/review/0")
    assert gone.status_code == 404 and "Back to where you were" not in gone.text
    assert ">Home</a>" not in gone.text
