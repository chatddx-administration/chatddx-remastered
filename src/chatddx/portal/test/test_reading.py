import json

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from chatddx.identity import Person
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.store import People
from chatddx.store.store import Connection


@pytest.fixture
def template(ran: str) -> str:
    return ran


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def shown(client: TestClient, path: str) -> str:
    got = client.get(path)
    assert got.status_code == 200, (path, got.text[:500])
    assert got.headers["content-type"].startswith("text/html")
    assert got.headers["cache-control"] == "no-store"
    return got.text


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
        assert escape(r["described"]) in page
        for item in detail["items"]:
            assert f">{item['outcome']}</span>" in page
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
def test_configurations_are_listed_by_purpose_and_read_with_their_recipe(
    signed: TestClient,
) -> None:
    query = {"kind": "configuration"}
    generation = signed.get("/api/threads", params=query).json()
    judges = signed.get("/api/threads", params={**query, "purpose": "judge"}).json()
    listed = shown(signed, "/configurations")
    judged = shown(signed, "/configurations?purpose=judge")
    for c in generation:
        assert f'href="/configurations/{c["id"]}"' in listed
    for c in judges:
        assert f'href="/configurations/{c["id"]}"' in judged
    [first, *_] = generation
    page = shown(signed, f"/configurations/{first['id']}")
    parts = signed.get(f"/api/threads/{first['id']}/variation").json()["parts"]
    for part in parts:
        if part["title"]:
            assert escape(part["title"]) in page
    assert "Version 1" in page
    scorer = signed.get("/api/threads", params={"kind": "scorer"}).json()[0]
    assert signed.get(f"/configurations/{scorer['id']}").status_code == 404


@pytest.mark.slow
def test_families_are_listed_by_tag_and_read_with_their_cases_and_vignette(
    signed: TestClient,
) -> None:
    families = signed.get("/api/families").json()
    listed = shown(signed, "/families")
    for f in families:
        assert f'href="/families/{f["id"]}"' in listed
    tagged = signed.get("/api/families", params={"tag": "swedish"}).json()
    page = shown(signed, "/families?tag=swedish")
    assert {f["id"] for f in families if f'href="/families/{f["id"]}"' in page} == {
        f["id"] for f in tagged
    }
    [noted] = [f for f in families if f["name"] == "noted"]
    page = shown(signed, f"/families/{noted['id']}")
    for case in signed.get(f"/api/families/{noted['id']}").json()["cases"]:
        for expected in case["expectations"]:
            assert escape(expected["title"]) in page
    vignette = signed.get(f"/api/families/{noted['id']}/vignette").json()
    page = shown(signed, f"/families/{noted['id']}/vignette")
    assert escape(vignette["text"].strip().splitlines()[0]) in page


@pytest.mark.slow
def test_endpoints_and_models_are_listed(signed: TestClient) -> None:
    page = shown(signed, "/endpoints")
    for e in signed.get("/api/endpoints").json():
        assert escape(e["name"]) in page
    for m in signed.get("/api/models").json():
        assert escape(m["name"]) in page


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
