import html
import time
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from fastapi.testclient import TestClient

from chatddx import settings
from chatddx.inventory import Inventory
from chatddx.portal.test.helpers import settled, shown, started, world_served
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, OFF, faked

__all__ = ["world_served"]


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
def test_a_case_is_run_from_its_review_under_each_configuration_that_runs(
    signed: TestClient,
) -> None:
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    back = f"/review/{crlf['id']}?tag=targets"
    form = {"case": crlf["case"], "back": back}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form)
    assert got.status_code == 303
    location = urlsplit(got.headers["location"])
    query = parse_qs(location.query)
    assert (location.path, location.fragment) == (f"/review/{crlf['id']}", "")
    assert (query["tag"], query["case"]) == (["targets"], [crlf["case"]])
    runs = reaching(signed, crlf)
    by: dict[int, list[dict[str, Any]]] = {}
    for r in runs:
        by.setdefault(r["ran"]["configuration"], []).append(r)
    for held in by.values():
        three, one = sorted(held, key=lambda r: -len(r["seeds"]))
        assert (len(three["seeds"]), len(one["seeds"])) == (3, 1)
        assert three["cases"] == one["cases"] == [crlf["case"]]
        if not three["titled"]["greedy"]:
            assert one["seeds"] == three["seeds"][-1:]
    query = {"kind": "configuration", "purpose": "generation", "owner": "alice"}
    owned = {t["id"] for t in signed.get("/api/threads", params=query).json()}
    assert by and set(by) <= owned
    for r in runs:
        _ = settled(signed, r["id"])

    page = shown(signed, f"{back}&case={crlf['case']}")
    assert 'id="evaluating"' not in page and "review-evaluation" not in page
    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form, headers=elsewhere)
    assert got.status_code == 403


def reaching(signed: TestClient, family: dict[str, Any]) -> list[dict[str, Any]]:
    query = {"reaching": family["case"], "limit": 200}
    return signed.get("/api/runs", params=query).json()


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_case_s_review_runs_no_other_while_one_is_open(signed: TestClient) -> None:
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    review = f"/review/{crlf['id']}?case={crlf['case']}"
    form = {"case": crlf["case"], "back": review}
    assert '<button class="run">' in shown(signed, review)
    assert signed.post("/queue/pause").status_code == 303
    assert signed.post(f"/review/{crlf['id']}/runs", data=form).status_code == 303
    runs = reaching(signed, crlf)
    assert runs
    assert signed.post(f"/review/{crlf['id']}/runs", data=form).status_code == 303
    assert len(reaching(signed, crlf)) == len(runs)
    assert '<button class="run" disabled>' in shown(signed, review)
    assert signed.post("/queue/resume").status_code == 303
    for r in runs:
        _ = settled(signed, r["id"])
    assert '<button class="run">' in shown(signed, review)


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_review_starts_nothing_over_the_quota(
    signed: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    review = f"/review/{crlf['id']}?case={crlf['case']}"
    monkeypatch.setattr(settings, "RUNS_PER_DAY", 1)
    form = {"case": crlf["case"], "back": review}
    got = signed.post(f"/review/{crlf['id']}/runs", data=form)
    assert got.status_code == 429
    assert "as many as a day takes" in html.unescape(got.text) or (
        "a day takes 1" in html.unescape(got.text)
    )
    assert signed.get("/api/runs").json() == []
