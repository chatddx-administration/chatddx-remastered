import json
import time
from typing import Any
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from chatddx.inventory import Inventory
from chatddx.portal.test.helpers import shown, world_served
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import GPT_OSS, GPT_OSS_ARTIFACT, LINES, OFF, faked

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


def _review_props(page: str) -> dict[str, Any]:
    held = page.split('<script type="application/json" id="review-props">', 1)[1]
    return json.loads(held.split("</script>", 1)[0])


@pytest.mark.slow
def test_a_case_is_run_from_its_review_and_followed_there(
    signed: TestClient, world: Inventory, conn: Connection
) -> None:
    query = {"kind": "configuration", "name": LINES, "owner": "alice"}
    [lines] = signed.get("/api/threads", params=query).json()
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    back = f"/review/{crlf['id']}"
    form = {
        "configuration": str(lines["id"]),
        "case": crlf["case"],
        "replicates": "2",
        "score": "true",
        "back": back,
    }
    with faked(world, Store(conn).get, delay=0.2):
        got = signed.post(f"/review/{crlf['id']}/runs", data=form)
        assert (got.status_code, got.headers["location"]) == (303, f"{back}#record")
        [run] = signed.get("/api/runs", params={"reaching": crlf["case"]}).json()
        page = shown(signed, back)
        assert 'data-pending="0"' in page and "1 under way" in page
        assert _review_props(page)["pending"] == [
            {"run": run["id"], "titled": run["titled"]}
        ]
        _ = settled(signed, run["id"])
    page = shown(signed, back)
    given = _review_props(page)
    assert given["pending"] == [] and 'data-pending="0"' not in page
    assert [(a["run"], a["replicate"]) for a in given["answers"]] == [
        (run["id"], 0),
        (run["id"], 1),
    ]

    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    for action in ("runs", "scores"):
        refused = signed.post(f"/review/{crlf['id']}/{action}", headers=elsewhere)
        assert refused.status_code == 403
    form["case"] = "sha256:" + "0" * 64
    assert signed.post(f"/review/{crlf['id']}/runs", data=form).status_code == 422


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_case_s_runs_are_scored_again_from_its_review_once_expected_otherwise(
    signed: TestClient,
) -> None:
    run = started(signed)
    _ = settled(signed, run)
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    query = {"kind": "scorer", "name": LINES}
    [scorer] = signed.get("/api/threads", params=query).json()
    back = f"/review/{crlf['id']}?scorer={scorer['id']}"
    page = shown(signed, back)
    assert f'action="/review/{crlf["id"]}/scores"' not in page

    [case] = signed.get(f"/api/families/{crlf['id']}").json()["cases"]
    [expected] = case["expectations"]
    query = {"kind": "expectation", "owner": "alice"}
    mine = next(
        t
        for t in signed.get("/api/threads", params=query).json()
        if t["head"]["digest"] == expected["expectation"]
    )
    data = {**expected["data"], "diagnosis": {"pattern": "subdural"}}
    component = {
        "kind": "expectation",
        "case": crlf["case"],
        "expectation_schema": expected["expectation_schema"],
        "data": data,
    }
    edit = {"head": mine["head"]["id"], "component": component}
    assert signed.post(f"/api/threads/{mine['id']}/edits", json=edit).status_code == 201

    def left() -> list[str]:
        listed = signed.get("/api/runs", params={"unscored": True}).json()
        return [u["scorer"] for r in listed if r["id"] == run for u in r["unscored"]]

    page = shown(signed, back)
    lines = scorer["head"]["digest"]
    assert f'action="/review/{crlf["id"]}/scores"' in page
    assert f'name="run" value="{run}"' in page and "1 to score" in page
    assert f'name="scorer" value="{lines}"' in page
    others = [s for s in left() if s != lines]
    assert others and lines in left()
    form = {"run": run, "scorer": lines, "back": back}
    got = signed.post(f"/review/{crlf['id']}/scores", data=form)
    assert (got.status_code, got.headers["location"]) == (303, f"{back}#record")
    for _ in range(500):
        page = shown(signed, back)
        if "to score" not in page and 'data-pending="0"' not in page:
            break
        time.sleep(0.02)
    assert f'action="/review/{crlf["id"]}/scores"' not in page
    assert left() == others
    scored = signed.get(f"/api/runs/{run}").json()["job"]
    got = signed.post(f"/review/{crlf['id']}/scores", data=form)
    assert (got.status_code, got.headers["location"]) == (303, f"{back}#record")
    assert signed.get(f"/api/runs/{run}").json()["job"] == scored


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_runs_with_something_under_way_are_scored_again_by_one_press_of_many(
    signed: TestClient,
) -> None:
    first, second = started(signed, score=False), started(signed, score=False)
    for run in (first, second):
        _ = settled(signed, run)
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    query = {"kind": "scorer", "name": LINES}
    [scorer] = signed.get("/api/threads", params=query).json()
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

    back = f"/review/{crlf['id']}?scorer={scorer['id']}"
    form = {"run": [first, second], "scorer": scorer["head"]["digest"], "back": back}
    got = signed.post(f"/review/{crlf['id']}/scores", data=form)
    assert (got.status_code, got.headers["location"]) == (303, f"{back}#record")
    assert signed.get(f"/api/runs/{first}").json()["job"] == held
    assert signed.get(f"/api/runs/{second}").json()["job"]["status"] == "queued"


@pytest.mark.slow
def test_a_case_run_from_its_review_under_another_model_runs_with_that_model(
    signed: TestClient, world: Inventory, conn: Connection
) -> None:
    query = {"kind": "configuration", "name": LINES, "owner": "alice"}
    [lines] = signed.get("/api/threads", params=query).json()
    [crlf] = signed.get("/api/families", params={"name": "crlf"}).json()
    [gpt_oss] = [
        m for m in signed.get("/api/models").json() if m["name"] == GPT_OSS_ARTIFACT
    ]
    form = {
        "configuration": str(lines["id"]),
        "case": crlf["case"],
        "model": GPT_OSS_ARTIFACT,
        "back": f"/review/{crlf['id']}",
    }
    with faked(world, Store(conn).get, endpoint=GPT_OSS):
        got = signed.post(f"/review/{crlf['id']}/runs", data=form)
        assert got.status_code == 303, got.text
        [run] = signed.get("/api/runs", params={"reaching": crlf["case"]}).json()
        _ = settled(signed, run["id"])
    assert (run["endpoint"], run["model"], run["latest"]) == (
        GPT_OSS,
        GPT_OSS_ARTIFACT,
        True,
    )
    assert run["ran"]["parts"] == {"model": gpt_oss["weights"]}
    assert run["described"].startswith(f"{LINES}+model=")
