import json
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from chatddx.portal.test.helpers import (
    ran_template,
    run_title,
    shown,
    variation_props,
)
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import TEST

__all__ = ["ran_template"]


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_a_run_is_titled_by_its_parts_in_the_locale_asked_for(
    signed: TestClient,
) -> None:
    [run] = [
        r
        for r in signed.get("/api/runs").json()
        if r["titled"]["case"]
        and not r["titled"]["case"]["appendices"]
        and len(r["seeds"]) == 1
        and not r["titled"]["greedy"]
    ][:1]
    titled = run["titled"]
    asked = signed.get(f"/runs/{run['id']}", headers={"accept-language": "sv"})
    case = titled["case"]["name"]
    swedish = (
        f"{case} med `{titled['name']}` på {titled['at']} (seed {run['seeds'][0]})"
    )
    assert escape(swedish) in asked.text
    assert escape(run_title(run)) in shown(signed, f"/runs/{run['id']}")


@pytest.mark.slow
def test_a_person_s_runs_are_listed_and_each_is_read_on_its_page(
    signed: TestClient,
) -> None:
    runs = signed.get("/api/runs").json()
    assert runs
    listed = shown(signed, "/runs")
    left = {r["id"] for r in signed.get("/api/runs", params={"unscored": True}).json()}
    listed_left = shown(signed, "/runs?left=true")
    for r in runs:
        assert f'href="/runs/{r["id"]}"' in listed
        assert (f'href="/runs/{r["id"]}"' in listed_left) == (r["id"] in left)
        page = shown(signed, f"/runs/{r['id']}")
        detail = signed.get(f"/api/runs/{r['id']}").json()
        assert escape(run_title(r)) in page
        for item in detail["items"]:
            assert f">{item['outcome']}</span>" in page
        row = listed.split(f'value="{r["id"]}"', 1)[1].split("</tr>", 1)[0]
        counted = Counter(item["outcome"] for item in detail["items"])
        assert all(f">{n} {said}</span>" in row for said, n in counted.items())
        if rest := len(r["cases"]) * len(r["seeds"]) - len(detail["items"]):
            assert f"{rest} {'missing' if r['finished'] else 'to go'}" in row
        for graded in detail["scores"]:
            assert escape(graded["name"]) in page
        assert 'id="item-1"' in page or not detail["items"]


@pytest.mark.slow
def test_a_run_s_page_shows_its_answers_and_what_its_scores_hold(
    signed: TestClient,
) -> None:
    runs = signed.get("/api/runs").json()
    judged = next(
        r for r in runs if signed.get(f"/api/runs/{r['id']}").json()["scores"]
    )
    page = shown(signed, f"/runs/{judged['id']}")
    for item in signed.get(f"/api/runs/{judged['id']}/items").json():
        answer = item["answer"]["value"]
        if isinstance(answer, str):
            assert escape(answer) in page
        elif answer is not None:
            assert escape(json.dumps(answer, indent=2, ensure_ascii=False)) in page
    assert ">Mean</td>" in page


@pytest.mark.slow
def test_a_first_mention_is_shown_where_it_is_in_the_answer(signed: TestClient) -> None:
    for r in signed.get("/api/runs").json():
        for graded in signed.get(f"/api/runs/{r['id']}").json()["scores"]:
            body = signed.get(f"/api/components/{graded['scorer']}").json()["body"]
            at = {
                i for i, v in enumerate(body["views"]) if v["metric"] == "first_mention"
            }
            found = [
                i["value"]
                for i in graded["items"]
                if i["view"] in at and i["value"] is not None
            ]
            if found:
                page = shown(signed, f"/runs/{r['id']}")
                assert all(f">@{int(v)}</td>" in page for v in found)
                compared = shown(signed, f"/runs/compare?run={r['id']}")
                assert all(f">@{int(graded['means'][v])} " in compared for v in at)
                return
    pytest.fail("no run is scored with a first mention")


@pytest.mark.slow
def test_another_s_run_isn_t_found_by_a_page_or_the_api(
    client: TestClient, signed: TestClient, conn: Connection
) -> None:
    [run, *_] = signed.get("/api/runs").json()
    _ = signed.post("/sign-out")
    People(conn).set_password(People(conn).add("bob", "Bob").id, "bob's password")
    form = {"login": "bob", "password": "bob's password", "next": "/"}
    assert client.post("/sign-in", data=form).status_code == 303
    page = client.get(f"/runs/{run['id']}")
    assert page.status_code == 404 and page.headers["content-type"].startswith(
        "text/html"
    )
    assert "Not found" in page.text and f"no run {run['id']} of yours" in page.text
    api = client.get(f"/api/runs/{run['id']}")
    assert (api.status_code, api.json()["code"]) == (404, "not_found")


@pytest.mark.slow
def test_a_configuration_is_read_with_its_recipe_in_the_lab(
    signed: TestClient,
) -> None:
    query = {"kind": "configuration"}
    [first, *_] = signed.get("/api/threads", params=query).json()
    page = shown(signed, f"/lab/{first['id']}")
    parts = signed.get(f"/api/threads/{first['id']}/variation").json()["parts"]
    assert variation_props(page)["look"]["parts"] == parts
    assert "Version 1" in page and "take scripts" in page
    scorer = signed.get("/api/threads", params={"kind": "scorer"}).json()[0]
    assert signed.get(f"/lab/{scorer['id']}").status_code == 404


@pytest.mark.slow
def test_cases_are_listed_by_tag_in_the_library_and_read_without_their_vignette(
    signed: TestClient,
) -> None:
    families = signed.get("/api/families").json()
    listed = shown(signed, "/library?kind=case")
    assert "None is begun here" in listed
    for f in families:
        assert f'href="/cases/{f["id"]}"' in listed
    tagged = signed.get("/api/families", params={"tag": "swedish"}).json()
    page = shown(signed, "/library?kind=case&tag=swedish")
    assert {f["id"] for f in families if f'href="/cases/{f["id"]}"' in page} == {
        f["id"] for f in tagged
    }
    [noted] = [f for f in families if f["name"] == "noted"]
    vignette = signed.get(f"/api/families/{noted['id']}/vignette").json()
    first = escape(vignette["text"].strip().splitlines()[0])
    page = shown(signed, f"/cases/{noted['id']}")
    assert first not in page and f'href="/cases/{noted["id"]}/vignette"' in page
    for case in signed.get(f"/api/families/{noted['id']}").json()["cases"]:
        for expected in case["expectations"]:
            assert escape(expected["title"]) in page
    assert first in shown(signed, f"/cases/{noted['id']}/vignette")
    assert signed.get("/families").status_code == 404


@pytest.mark.slow
def test_the_world_lists_what_the_portal_started_in_and_its_models_by_handle(
    signed: TestClient,
) -> None:
    page = shown(signed, "/world")
    assert str(TEST / "inventory.toml") in page and str(TEST / "facts.toml") in page
    for m in signed.get("/api/models").json():
        assert escape(m["name"]) in page
    for e in signed.get("/api/endpoints").json():
        assert escape(e["name"]) in page and escape(e["url"]) in page
    assert str(TEST / "vignettes") in page and "texts typed into the database" in page
    assert "CHATDDX_TEST_REMOTE" in page and "Qwen/Qwen3-8B-AWQ" in page
    assert '<span class="font-medium">verdict</span> to qwen3-8b-awq' in page
    assert 'href="/world"' in page and signed.get("/models").status_code == 404


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_what_a_page_can_t_find_is_a_page_and_the_api_s_stays_json(
    signed: TestClient,
) -> None:
    page = signed.get("/nowhere")
    assert page.status_code == 404 and "Not found" in page.text
    assert "aria-current" not in page.text and "Sign out" in page.text
    assert signed.get("/api/nowhere").json()["code"] == "not_found"
    assert signed.get("/runs/not-a-run").status_code == 422
