import html
import json
import re
import time
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.helpers import digest, thread
from chatddx.inventory import Inventory
from chatddx.portal.test.helpers import props, shown, world_served
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, OFF, faked

__all__ = ["world_served"]


def started(signed: TestClient, **more: Any) -> str:
    query = {"kind": "configuration", "name": LINES, "owner": "alice"}
    [lines] = signed.get("/api/threads", params=query).json()
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    body = {"configuration": lines["id"], "families": [crlf["id"]]}
    got = signed.post("/api/runs", json={**body, **more})
    assert got.status_code == 202, got.json()
    return got.json()["runs"][0]["run"]


def settled(signed: TestClient, run: str) -> dict[str, Any]:
    for _ in range(500):
        if "under way" not in shown(signed, f"/runs/{run}"):
            found = signed.get(f"/api/runs/{run}").json()
            if found["finished"]:
                return found
        time.sleep(0.02)
    raise AssertionError(f"run {run} is still under way")


@pytest.mark.slow
def test_a_run_under_way_is_followed_and_halted_on_its_page(
    signed: TestClient, world: Inventory, conn: Connection
) -> None:
    with faked(world, Store(conn).get, delay=0.2):
        run = started(signed)
        page = shown(signed, f"/runs/{run}")
        assert "Something is under way for this run" in page
        assert 'id="run-live-props"' in page and f'"run": "{run}"' in page
        assert f'action="/runs/{run}/halt"' in page
        assert "Run again" not in page and "Items</h2>" not in page

        got = signed.post(f"/runs/{run}/halt")
        assert (got.status_code, got.headers["location"]) == (303, f"/runs/{run}")
        _ = settled(signed, run)

    page = shown(signed, f"/runs/{run}")
    assert "Items</h2>" in page and 'id="run-live"' not in page
    assert f'action="/runs/{run}/halt"' not in page
    assert f'action="/runs/{run}/scores"' in page and "Left to score by" in page
    assert f'action="/runs/{run}/again"' in page
    left = shown(signed, "/runs?left=true")
    assert f'action="/runs/{run}/scores"' in left

    stale = signed.post(f"/runs/{run}/halt")
    assert (stale.status_code, stale.headers["location"]) == (303, f"/runs/{run}")


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_is_scored_again_and_run_again_from_its_page(signed: TestClient) -> None:
    run = started(signed, score=False)
    _ = settled(signed, run)
    assert "Left to score by" in shown(signed, f"/runs/{run}")

    got = signed.post(f"/runs/{run}/scores")
    assert (got.status_code, got.headers["location"]) == (303, f"/runs/{run}")
    scored = settled(signed, run)
    assert scored["scores"] and "Left to score by" not in shown(signed, f"/runs/{run}")
    stale = signed.post(f"/runs/{run}/scores")
    assert (stale.status_code, stale.headers["location"]) == (303, f"/runs/{run}")
    assert signed.get(f"/api/runs/{run}").json()["job"] == scored["job"]

    got = signed.post(f"/runs/{run}/again")
    assert got.status_code == 303
    again = got.headers["location"].removeprefix("/runs/")
    assert again != run
    shown_again = settled(signed, again)
    assert (shown_again["skeleton"], shown_again["cases"]) == (
        scored["skeleton"],
        scored["cases"],
    )
    assert (
        shown_again["described"].split(" (seed")[0]
        == scored["described"].split(" (seed")[0]
    )


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_links_the_variation_it_ran(signed: TestClient) -> None:
    query = {"kind": "reasoning", "name": OFF, "owner": "alice"}
    [off] = signed.get("/api/threads", params=query).json()
    parts = {"reasoning": off["head"]["digest"]}
    run = started(signed, parts=parts, score=False)
    ran = settled(signed, run)["ran"]
    page = shown(signed, f"/runs/{run}")
    tried = f"/lab/{ran['configuration']}?{urlencode(parts)}"
    assert f'href="{tried}">{LINES}+reasoning={OFF}<' in page


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_the_runs_page_says_how_the_queue_stands_and_pauses_stops_and_resumes_it(
    signed: TestClient,
) -> None:
    page = shown(signed, "/runs")
    assert "0 queued, 0 under way." in page and 'action="/queue/pause"' in page
    assert 'action="/queue/stop"' not in page

    got = signed.post("/queue/pause")
    assert (got.status_code, got.headers["location"]) == (303, "/runs")
    run = started(signed)
    page = shown(signed, "/runs")
    assert "1 queued, 0 under way; paused." in page
    assert 'action="/queue/resume"' in page and "queued, paused" in page
    assert ">Stop</button>" in page and ">Stop now</button>" not in page

    assert signed.post("/queue/stop").status_code == 303
    page = shown(signed, "/runs")
    assert "stopped: taken out of the queue" in page
    assert 'action="/queue/stop"' not in page
    page = shown(signed, f"/runs/{run}")
    assert f'action="/runs/{run}/resume"' in page and "Run again" in page

    for _ in range(2):
        got = signed.post(f"/runs/{run}/resume")
        assert (got.status_code, got.headers["location"]) == (303, f"/runs/{run}")
    assert signed.post("/queue/resume").status_code == 303
    _ = settled(signed, run)
    done = signed.get(f"/api/runs/{run}").json()
    assert done["finished"] and done["job"]["status"] == "finished"
    page = shown(signed, f"/runs/{run}")
    assert f'action="/runs/{run}/resume"' not in page
    stale = signed.post(f"/runs/{run}/resume")
    assert (stale.status_code, stale.headers["location"]) == (303, f"/runs/{run}")
    assert signed.get(f"/api/runs/{run}").json()["job"] == done["job"]


@pytest.mark.slow
def test_stop_now_halts_the_runs_under_way(
    signed: TestClient, world: Inventory, conn: Connection
) -> None:
    with faked(world, Store(conn).get, delay=0.2):
        run = started(signed)
        page = shown(signed, "/runs")
        for _ in range(500):
            if "1 under way" in page:
                break
            time.sleep(0.02)
            page = shown(signed, "/runs")
        assert ">Stop now</button>" in page and ">Stop</button>" not in page
        got = signed.post("/queue/stop", data={"now": "true"})
        assert got.status_code == 303
        _ = settled(signed, run)
    halted = signed.get(f"/api/runs/{run}").json()
    assert (halted["job"]["status"], halted["job"]["halt"]) == ("stopped", True)
    assert halted["scores"] == []


@pytest.mark.slow
def test_a_form_from_another_site_starts_nothing(signed: TestClient) -> None:
    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    for action in ("halt", "scores", "again", "resume"):
        got = signed.post(
            "/runs/00000000-0000-0000-0000-000000000000/" + action, headers=elsewhere
        )
        assert got.status_code == 403
    for action in ("pause", "resume", "stop"):
        assert signed.post(f"/queue/{action}", headers=elsewhere).status_code == 403


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_whose_scoring_is_queued_is_not_scored_again_by_another_press(
    signed: TestClient,
) -> None:
    first, second = started(signed, score=False), started(signed, score=False)
    for run in (first, second):
        _ = settled(signed, run)
    assert signed.post("/queue/pause").status_code == 303
    assert signed.post(f"/runs/{first}/scores").status_code == 303
    held = signed.get(f"/api/runs/{first}").json()["job"]
    assert held["status"] == "queued"
    left = shown(signed, "/runs?left=true")
    assert f'href="/runs/{first}"' in left
    assert f'action="/runs/{first}/scores"' not in left
    assert f'action="/runs/{second}/scores"' in left
    again = signed.post(f"/runs/{first}/scores")
    assert (again.status_code, again.headers["location"]) == (303, f"/runs/{first}")
    assert signed.get(f"/api/runs/{first}").json()["job"] == held


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_case_is_evaluated_from_its_review_under_each_configuration_that_runs(
    signed: TestClient,
) -> None:
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    back = f"/review/{crlf['id']}?tag=targets"
    form = {"case": crlf["case"], "back": back}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form)
    assert got.status_code == 303
    path, _, fragment = got.headers["location"].partition("#")
    query = parse_qs(urlsplit(path).query)
    assert fragment == "evaluating"
    assert (query["tag"], query["case"]) == (["targets"], [crlf["case"]])
    [first] = query["evaluation"]
    runs = signed.get("/api/runs", params={"with": first, "limit": 200}).json()
    by: dict[int, list[dict[str, Any]]] = {}
    for r in runs:
        by.setdefault(r["ran"]["configuration"], []).append(r)
    for held in by.values():
        three, one = sorted(held, key=lambda r: -len(r["seeds"]))
        assert (len(three["seeds"]), len(one["seeds"])) == (3, 1)
        assert three["cases"] == one["cases"] == [crlf["case"]]
        if not three["titled"]["greedy"]:
            assert one["seeds"] == three["seeds"][-1:]
    for r in runs:
        _ = settled(signed, r["id"])

    page = shown(signed, path)
    held = page.split('<script type="application/json" id="review-props">', 1)[1]
    given = json.loads(held.split("</script>", 1)[0])["evaluation"]
    assert given["first"] == first
    assert {c["configuration"] for c in given["configurations"]} == set(by)
    assert all(len(c["runs"]) == 2 for c in given["configurations"])
    assert given["fields"] == [
        "diagnosis",
        "warning",
        "disposition",
        "dont_miss",
        "notes",
    ]
    fields = {v["field"] for views in given["scorers"].values() for v in views}
    assert {"diagnosis", "dont_miss", "notes"} <= fields
    left = page.split("Left out:", 1)[1].split("</ul>", 1)[0]
    assert "tools can&#39;t be cleared yet" in left
    query = {"kind": "configuration", "purpose": "generation", "owner": "alice"}
    live = signed.get("/api/threads", params=query).json()
    assert len(by) + left.count("<li>") == len(live)
    every = {"kind": "configuration", "purpose": "generation"}
    assert len(signed.get("/api/threads", params=every).json()) > len(live)
    owned = {t["id"] for t in live}
    assert set(by) <= owned and "archive/" not in left

    [noted] = signed.get("/api/families", params={"name": "noted"}).json()
    assert signed.get(f"/review/{noted['id']}?evaluation={first}").status_code == 404
    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form, headers=elsewhere)
    assert got.status_code == 403


def evaluating(signed: TestClient, family: dict[str, Any]) -> str:
    form = {"case": family["case"], "back": f"/review/{family['id']}"}
    got = signed.post(f"/review/{family['id']}/runs", data=form)
    assert got.status_code == 303
    [first] = parse_qs(urlsplit(got.headers["location"]).query)["evaluation"]
    return first


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_case_s_review_shows_its_latest_runs_and_runs_no_other_while_one_is_open(
    signed: TestClient,
) -> None:
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    review = f"/review/{crlf['id']}?case={crlf['case']}"
    assert props(shown(signed, review))["evaluation"] is None
    assert signed.post("/queue/pause").status_code == 303
    first = evaluating(signed, crlf)
    assert evaluating(signed, crlf) == first
    runs = signed.get("/api/runs", params={"with": first, "limit": 200}).json()
    page = shown(signed, review)
    assert sorted(props(page)["busy"]) == sorted(r["id"] for r in runs)
    assert props(page)["evaluation"]["first"] is None
    assert re.search(r'<button class="run" disabled data-busy>', page)
    assert signed.post("/queue/resume").status_code == 303
    for r in runs:
        _ = settled(signed, r["id"])

    second = evaluating(signed, crlf)
    assert second != first
    for r in signed.get("/api/runs", params={"with": second, "limit": 200}).json():
        _ = settled(signed, r["id"])
    page = shown(signed, review)
    assert (props(page)["busy"], props(page)["evaluation"]["first"]) == (None, None)
    assert '<button class="run">' in page
    assert "Not as things are now" not in page and "data-rework" not in page
    assert linked(page, "prev") == [second] and linked(page, "next") == []
    page = shown(signed, f"{review}&evaluation={second}")
    assert props(page)["evaluation"]["first"] == second
    assert linked(page, "prev") == [first] and linked(page, "next") == [None]
    assert re.search(r'rel="prev" href="[^"]+">← \d{4}-\d\d-\d\d \d\d:\d\d<', page)
    assert "Latest →" in page
    page = shown(signed, f"{review}&evaluation={first}")
    assert linked(page, "prev") == [] and linked(page, "next") == [second]


def flagged(page: str) -> str:
    held = page.split("data-told", 1)[1].split('id="review-evaluation"', 1)[0]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", held))
    return html.unescape(text).replace(" :", ":")


def linked(page: str, rel: str) -> list[str | None]:
    found = re.findall(rf'<a rel="{rel}"[^>]* href="([^"]+)">', page)
    return [
        parse_qs(urlsplit(html.unescape(h)).query).get("evaluation", [None])[0]
        for h in found
    ]


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_the_latest_runs_flag_what_the_configuration_or_expectation_has_changed_since(
    signed: TestClient,
) -> None:
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    review = f"/review/{crlf['id']}?case={crlf['case']}"
    first = evaluating(signed, crlf)
    for r in signed.get("/api/runs", params={"with": first, "limit": 200}).json():
        _ = settled(signed, r["id"])
    assert "data-rework" not in shown(signed, review)

    off = digest(signed, "reasoning", OFF)
    lines = thread(signed, "configuration", LINES)
    edited = {"head": lines["head"]["id"], "parts": {"reasoning": off}}
    got = signed.post(f"/api/threads/{lines['id']}/edits", json=edited)
    assert got.status_code == 201
    page = shown(signed, review)
    told = flagged(page)
    assert f"{LINES}: its configuration has changed since it ran" in told
    assert "data-rework" in page and "Rework" in told
    assert "data-rework" not in shown(signed, f"{review}&evaluation={first}")

    [case] = signed.get(f"/api/families/{crlf['id']}").json()["cases"]
    [expected] = [e for e in case["expectations"] if e["expectation"]]
    query = {"kind": "expectation", "owner": "alice"}
    [mine] = [
        t
        for t in signed.get("/api/threads", params=query).json()
        if t["head"]["digest"] == expected["expectation"]
    ]
    held = signed.get(f"/api/components/{mine['head']['digest']}").json()["body"]
    warning = {"pattern": held["data"]["warning"]["pattern"] + " | apixaban"}
    changed = {**held, "data": {**held["data"], "warning": warning}}
    got = signed.post(
        f"/api/threads/{mine['id']}/edits",
        json={"head": mine["head"]["id"], "component": changed},
    )
    assert got.status_code == 201
    told = flagged(shown(signed, review))
    assert "isn't scored against the expectation as it is" in told
