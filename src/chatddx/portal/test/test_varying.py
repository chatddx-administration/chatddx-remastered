import json
from typing import Any
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape
from pydantic import JsonValue

from chatddx.bench import Bench
from chatddx.bench.test.helpers import correct_facts
from chatddx.factors.request import RECIPE_PARTS
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.store.store import Connection
from chatddx.test.world import LINES, OFF, QWEN, QWEN_MODEL, TEST


@pytest.fixture
def template(ran: str) -> str:
    return ran


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def thread(
    signed: TestClient, kind: str, name: str, owner: str = "alice"
) -> dict[str, Any]:
    query = {"kind": kind, "name": name, "owner": owner}
    [found] = signed.get("/api/threads", params=query).json()
    return found


def held(page: str) -> dict[str, Any]:
    opened = '<script type="application/json" id="variation-props">'
    return json.loads(page.split(opened, 1)[1].split("</script>", 1)[0])


@pytest.mark.slow
def test_a_configuration_s_page_holds_the_variation_its_address_gives(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    page = shown(
        signed, f"/configurations/{mine['id']}?reasoning={off}&endpoint={QWEN}"
    )
    assert escape(f"{LINES}+reasoning={OFF}") in page

    given = held(page)
    look = given["look"]
    api = f"/api/threads/{mine['id']}/variation"
    asked = signed.get(api, params={"reasoning": off}).json()
    assert (look["label"], look["skeleton"]) == (asked["label"], asked["skeleton"])
    assert given["base"]["reasoning"] is None
    recipe = signed.get(f"/api/threads/{mine['id']}").json()["recipe"]
    assert given["base"] == {p: recipe[p] for p in RECIPE_PARTS}
    assert set(given["choices"]) == set(RECIPE_PARTS)
    assert all("language" in t for p in RECIPE_PARTS for t in given["choices"][p])
    assert given["me"] == "alice" and given["configuration"]["id"] == mine["id"]

    assert given["endpoint"] == QWEN and look["findings"] is not None
    models = [t["head"]["digest"] for t in given["choices"]["model"]]
    assert recipe["model"] in models
    served = {e["serves"] for e in given["endpoints"]}
    assert set(models) <= served and len(models) == len(set(models))

    tagged = held(
        shown(signed, f"/configurations/{mine['id']}?endpoint={QWEN}&tag=targets")
    )
    assert (tagged["endpoint"], tagged["tags"]) == (QWEN, ["targets"])
    assert {r["cases"] for r in tagged["look"]["reach"]} != {0}


@pytest.mark.slow
def test_a_fork_links_the_configuration_it_was_forked_from(signed: TestClient) -> None:
    mine = thread(signed, "configuration", LINES)
    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    edits = f"/api/threads/{mine['id']}/edits"
    later = signed.post(
        edits, json={"head": mine["head"]["id"], "parts": {"reasoning": off}}
    )
    forks = f"/api/threads/{mine['id']}/forks"
    fork = signed.post(forks, json={"name": "terse"}).json()
    assert later.json()["id"] != mine["id"]

    page = shown(signed, f"/configurations/{fork['id']}")
    assert f'href="/configurations/{mine["id"]}">a fork</a>' in page
    archives = thread(signed, "configuration", LINES, "archive")
    assert ">a fork</a>" not in shown(signed, f"/configurations/{archives['id']}")


@pytest.mark.slow
def test_a_fork_follows_its_origin_from_its_page(signed: TestClient) -> None:
    mine = thread(signed, "configuration", LINES)
    off = thread(signed, "reasoning", OFF)
    forks = f"/api/threads/{mine['id']}/forks"
    fork = signed.post(
        forks, json={"name": "terse", "parts": {"reasoning": off["head"]["digest"]}}
    ).json()
    path = f"/configurations/{fork['id']}"
    assert "Its origin has moved on" not in shown(signed, path)

    greedy = thread(signed, "sampling", "greedy")["head"]["digest"]
    edits = f"/api/threads/{mine['id']}/edits"
    got = signed.post(
        edits, json={"head": mine["head"]["id"], "parts": {"sampling": greedy}}
    )
    assert got.status_code == 201
    page = shown(signed, path)
    assert "Its origin has moved on" in page
    assert f"reasoning</span>: yours keeps {OFF} over —" in page
    assert "Its origin has moved on" not in shown(
        signed, f"/configurations/{mine['id']}"
    )

    head = signed.get(f"/api/threads/{fork['id']}").json()["head"]
    got = signed.post(
        f"/threads/{fork['id']}/follow", data={"head": head["id"], "next": path}
    )
    assert (got.status_code, got.headers["location"]) == (303, path)
    assert "Its origin has moved on" not in shown(signed, path)
    followed = signed.get(f"/api/threads/{fork['id']}/variation").json()
    assert {p["part"]: p["digest"] for p in followed["parts"]}["sampling"] == greedy


@pytest.mark.slow
def test_a_configuration_follows_its_corrected_facts_from_its_page(
    signed: TestClient, conn: Connection, alice: Person
) -> None:
    mine = thread(signed, "configuration", LINES)
    path = f"/configurations/{mine['id']}"
    corrected = "What it was compiled for has moved on"
    assert corrected not in shown(signed, path)

    bench = Bench(conn, alice, Inventory.load(TEST / "inventory.toml"))
    recommended: dict[str, JsonValue] = {"on": {"temperature": 0.2}}
    _ = correct_facts(bench, QWEN_MODEL, sampling={"recommended": recommended})
    page = shown(signed, path)
    assert corrected in page and ">Follow<" in page

    got = signed.post(
        f"/threads/{mine['id']}/moved/follow",
        data={"head": mine["head"]["id"], "next": path},
    )
    assert (got.status_code, got.headers["location"]) == (303, path)
    assert corrected not in shown(signed, path)
    request = signed.get(f"/api/threads/{mine['id']}/variation").json()["request"]
    assert request["temperature"] == 0.2


@pytest.mark.slow
def test_its_versions_are_stepped_through_keeping_what_is_set(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    first = mine["head"]["id"]
    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    edits = f"/api/threads/{mine['id']}/edits"
    later = signed.post(edits, json={"head": first, "parts": {"reasoning": off}})
    latest = later.json()["id"]
    path = f"/configurations/{mine['id']}"

    greedy = thread(signed, "sampling", "greedy")["head"]["digest"]
    page = shown(signed, f"{path}?head={first}&sampling={greedy}")
    assert "Version 1 of 2" in page and "A newer version is saved" in page
    kept = urlencode({"sampling": greedy})
    assert f'href="?{kept}" data-head="{latest}"' in page
    assert held(page)["look"]["head"]["id"] == first

    page = shown(signed, path)
    assert "Version 2 of 2" in page and "A newer version is saved" not in page
    assert f'href="?head={first}" data-head="{first}"' in page
    assert held(page)["base"]["reasoning"] == off


@pytest.mark.slow
def test_a_variation_the_bench_refuses_is_a_page_of_its_own(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    archives = thread(signed, "configuration", LINES, "archive")
    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    path = f"/configurations/{mine['id']}"
    for query, status, said in (
        (f"prompt={off}", 422, f"{off} isn&#39;t a stored chunk of prompt"),
        (f"head={archives['head']['id']}", 404, "no edit"),
        ("stack=x", 422, "query.stack: Extra inputs are not permitted"),
    ):
        got = signed.get(f"{path}?{query}")
        assert got.status_code == status, query
        assert got.headers["content-type"].startswith("text/html")
        assert said in got.text, (query, got.text[:2000])


@pytest.mark.slow
def test_the_runs_of_the_variation_are_on_its_page(signed: TestClient) -> None:
    runs = signed.get("/api/runs", params={"limit": 200}).json()
    configurations = signed.get(
        "/api/threads", params={"kind": "configuration", "owner": "alice"}
    ).json()
    heads = {c["head"]["digest"]: c for c in configurations}
    run = next(r for r in runs if r["skeleton"] in heads)
    page = shown(signed, f"/configurations/{heads[run['skeleton']]['id']}")
    assert f'href="/runs/{run["id"]}"' in page
    assert run["id"] in {r["id"] for r in held(page)["runs"]}


@pytest.mark.slow
def test_a_run_links_the_version_it_ran_else_one_holding_its_skeleton(
    signed: TestClient,
) -> None:
    runs = signed.get("/api/runs", params={"limit": 200}).json()
    configurations = signed.get(
        "/api/threads", params={"kind": "configuration", "owner": "alice"}
    ).json()
    heads = {c["head"]["digest"]: c for c in configurations}
    run = next(r for r in runs if r["skeleton"] in heads)
    ran = heads[run["skeleton"]]
    assert f'href="/configurations/{ran["id"]}"' in shown(signed, f"/runs/{run['id']}")

    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    edits = f"/api/threads/{ran['id']}/edits"
    got = signed.post(
        edits, json={"head": ran["head"]["id"], "parts": {"reasoning": off}}
    )
    assert got.status_code == 201
    page = shown(signed, f"/runs/{run['id']}")
    assert f'href="/configurations/{ran["id"]}?head={ran["head"]["id"]}"' in page
    assert "an earlier version" in page

    deleted = signed.patch(f"/api/threads/{ran['id']}", json={"deleted": True})
    assert deleted.status_code == 200
    archives = thread(signed, "configuration", ran["name"], "archive")
    page = shown(signed, f"/runs/{run['id']}")
    assert f'href="/configurations/{archives["id"]}"' in page
