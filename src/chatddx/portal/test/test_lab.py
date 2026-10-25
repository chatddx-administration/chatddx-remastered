import re
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from markupsafe import escape
from pydantic import JsonValue

from chatddx.api.test.helpers import thread
from chatddx.bench import Bench
from chatddx.bench.test.helpers import correct_facts
from chatddx.catalog.titles import display_digest
from chatddx.factors.engine import FileDigest, LocalModel
from chatddx.factors.request import RECIPE_PARTS
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.locale import Locales
from chatddx.locale.test.helpers import catalog
from chatddx.portal.test.helpers import ran_template, said, shown, variation_props
from chatddx.scripted.test.helpers import held
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection
from chatddx.test.helpers import alices_bench
from chatddx.test.world import (
    COMPARED,
    GPT_OSS_ARTIFACT,
    JUDGE,
    LINES,
    LINES_GUIDED,
    LINES_INSTRUCTED,
    OFF,
    QWEN_ARTIFACT,
    QWEN_MODEL,
    TEST,
)

__all__ = ["alices_bench", "ran_template"]


@pytest.mark.slow
def test_the_lab_leads_to_one_s_first_configuration(signed: TestClient) -> None:
    got = signed.get("/lab")
    assert got.status_code == 303
    listed = signed.get(
        "/api/threads", params={"kind": "configuration", "owner": "alice"}
    ).json()
    first = min(listed, key=lambda t: t["name"] or t["title"])
    assert got.headers["location"] == f"/lab/{first['id']}"
    assert 'href="/lab"' in shown(signed, "/runs")


@pytest.mark.slow
def test_a_configuration_s_lineage_fares_side_by_side_on_a_set(
    signed: TestClient, bench: Bench
) -> None:
    mine = thread(signed, "configuration", LINES_INSTRUCTED)
    instructed, _, guided = (held(bench, name).run for name in COMPARED)
    page = shown(signed, f"/lab/{mine['id']}")
    text = said(page)

    assert re.search(
        rf"Lineage 4 archive/{LINES_INSTRUCTED} 0\.75 {LINES_INSTRUCTED} 0\.75 "
        + rf"archive/{LINES_GUIDED} 0\.00 varies [^·]*few shot[^·]* {LINES_GUIDED} 0\.00",
        text,
    )
    assert f'href="/runs/{instructed}"' in page and f'href="/runs/{guided}"' in page
    assert page.index(f"/runs/{instructed}") < page.index(f"/runs/{guided}")
    assert re.search(r"lines · differential 0\.75 \(2\) 0\.00 \(2\)", text)
    assert "each column is its latest run of yours at its model's latest engine" in text
    assert f"under {QWEN_ARTIFACT}" in text

    whole = signed.get(f"/api/runs/{instructed}/scores").json()
    [lines] = [g for g in whole if g["name"] == LINES]
    by = f"{lines['scorer']}:2"
    page = shown(signed, f"/lab/{mine['id']}?by={by}")
    assert re.search(r"Lineage 4 \S+ — ", said(page))

    page = shown(signed, f"/lab/{mine['id']}?tag=targets")
    text = said(page)
    assert "not run" in text
    assert "None of them has a run at its model's latest engine yet." in text
    forced = said(shown(signed, f"/lab/{mine['id']}?handle={GPT_OSS_ARTIFACT}"))
    assert (
        f"under {GPT_OSS_ARTIFACT}" in forced and f"under {QWEN_ARTIFACT}" not in forced
    )
    assert "not run" in forced


@pytest.mark.slow
def test_a_column_whose_weights_its_handle_no_longer_holds_says_so(
    signed: TestClient, bench: Bench
) -> None:
    store = Store(bench.conn)
    registry = store.load([])
    weights = registry.add(
        LocalModel(
            repo=QWEN_MODEL,
            revision="newer",
            files=(FileDigest(path="none", sha256="0" * 64),),
        )
    )
    _ = store.add(registry, [weights])
    handle = bench.handle_named(QWEN_ARTIFACT)
    _ = Catalog(bench.conn).edit(handle.thread, weights, bench.person.id)
    bench.conn.commit()
    mine = thread(signed, "configuration", LINES_INSTRUCTED)
    text = said(shown(signed, f"/lab/{mine['id']}"))
    assert "out of date" in text
    assert "None of them has a run at its model's latest engine yet." in text


@pytest.mark.slow
def test_weights_no_model_thread_holds_are_a_whoops_where_they_are_tried(
    signed: TestClient, paged: TestClient, bench: Bench, served: FastAPI, tmp_path: Path
) -> None:
    store = Store(bench.conn)
    registry = store.load([])
    weights = registry.add(
        LocalModel(
            repo=QWEN_MODEL,
            revision="unheld",
            files=(FileDigest(path="none", sha256="0" * 64),),
        )
    )
    _ = store.add(registry, [weights])
    bench.conn.commit()
    lines = thread(signed, "configuration", LINES)
    whoops = "The model has no handle and can't be used."
    pass_on = (
        f"{display_digest(weights)} is held by no model thread: check the RuntimeErrors"
    )
    got = paged.get(f"/lab/{lines['id']}?model={weights}")
    assert got.status_code == 500, said(got.text)[:300]
    assert said(got.text).startswith(
        f"> That shouldn't have happened {escape(whoops)} Copy this and send it to "
        + f"drift@chatddx.com: {pass_on} "
    )
    asked = paged.get(f"/api/threads/{lines['id']}/variation?model={weights}")
    assert (asked.status_code, asked.json()) == (
        500,
        {"code": "whoops", "detail": whoops, "pass_on": pass_on},
    )

    served.state.locales = Locales(
        catalog(
            tmp_path,
            f"""
            msgctxt "whoops"
            msgid "{whoops}"
            msgstr "Ingen modell i biblioteket håller vikterna: ta en annan så länge."
            """,
        )
    )
    sv = paged.get(
        f"/lab/{lines['id']}?model={weights}", headers={"accept-language": "sv"}
    )
    assert (
        f"Ingen modell i biblioteket håller vikterna: ta en annan så länge. Copy this and send it to drift@chatddx.com: {pass_on} "
        in said(sv.text)
    )


@pytest.mark.slow
def test_a_judge_s_configuration_is_tried_but_not_fared_and_a_chunk_isn_t_found(
    signed: TestClient,
) -> None:
    prompt = thread(signed, "prompt", "case")
    assert signed.get(f"/lab/{prompt['id']}").status_code == 404
    judge = signed.get(
        "/api/threads",
        params={"kind": "configuration", "purpose": "judge", "name": JUDGE},
    ).json()[0]
    page = shown(signed, f"/lab/{judge['id']}")
    assert "A judge's configuration isn't run on cases" in page
    assert 'aria-label="How they fare"' not in page and "Its trials" not in page
    given = variation_props(page)
    assert (given["configuration"]["id"], given["judged"]) == (judge["id"], True)
    lines = thread(signed, "configuration", LINES)
    assert variation_props(shown(signed, f"/lab/{lines['id']}"))["judged"] is False
    assert signed.get(f"/lab/{lines['id']}?handle=nowhere").status_code == 422


@pytest.mark.slow
def test_runs_picked_on_the_runs_page_are_compared(
    signed: TestClient, bench: Bench
) -> None:
    runs = [held(bench, name).run for name in COMPARED]
    page = shown(signed, "/runs")
    assert 'action="/runs/compare"' in page
    assert f'name="run" value="{runs[0]}" form="compare"' in page

    query = "&".join(f"run={r}" for r in runs)
    text = said(shown(signed, f"/runs/compare?{query}"))
    assert re.search(r"lines · differential 0\.75 \(2\) 0\.50 \(2\) 0\.00 \(2\)", text)
    assert re.search(r"By item, under \w+ · [\w-]+ ", text)
    assert "Held by only some" not in text
    appendix = held(bench, "appendix").run
    text = said(shown(signed, f"/runs/compare?run={runs[0]}&run={appendix}"))
    assert "A mean is over the 0 items" in text and "By item" not in text
    assert "Held by only some" in text
    assert signed.get("/runs/compare").status_code == 422


@pytest.mark.slow
def test_the_lab_holds_the_variation_its_address_gives(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    page = shown(signed, f"/lab/{mine['id']}?reasoning={off}")
    assert escape(f"{LINES}+reasoning={OFF}") in page

    given = variation_props(page)
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

    assert given["under"] is None and look["findings"] is not None
    assert (look["model"], look["problem"]) == (QWEN_ARTIFACT, None)
    models = [t["head"]["digest"] for t in given["choices"]["model"]]
    assert recipe["model"] in models
    handles = {t["name"] for t in given["choices"]["model"]}
    assert handles == set(given["models"]) and len(models) == len(set(models))

    tagged = variation_props(shown(signed, f"/lab/{mine['id']}?tag=targets"))
    assert (tagged["under"], tagged["tags"]) == (None, ["targets"])
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

    page = shown(signed, f"/lab/{fork['id']}")
    assert f'href="/lab/{mine["id"]}">a fork</a>' in page
    archives = thread(signed, "configuration", LINES, "archive")
    assert ">a fork</a>" not in shown(signed, f"/lab/{archives['id']}")


@pytest.mark.slow
def test_a_fork_follows_its_origin_from_its_page(signed: TestClient) -> None:
    mine = thread(signed, "configuration", LINES)
    off = thread(signed, "reasoning", OFF)
    forks = f"/api/threads/{mine['id']}/forks"
    fork = signed.post(
        forks, json={"name": "terse", "parts": {"reasoning": off["head"]["digest"]}}
    ).json()
    path = f"/lab/{fork['id']}"
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
    assert "Its origin has moved on" not in shown(signed, f"/lab/{mine['id']}")

    head = signed.get(f"/api/threads/{fork['id']}").json()["head"]
    got = signed.post(
        f"/threads/{fork['id']}/follow", data={"head": head["id"], "next": path}
    )
    assert (got.status_code, got.headers["location"]) == (303, path)
    assert "Its origin has moved on" not in shown(signed, path)
    followed = signed.get(f"/api/threads/{fork['id']}/variation").json()
    assert {p["part"]: p["digest"] for p in followed["parts"]}["sampling"] == greedy


@pytest.mark.slow
def test_a_configuration_follows_its_corrected_facts_from_its_pages(
    signed: TestClient, conn: Connection, alice: Person
) -> None:
    mine = thread(signed, "configuration", LINES)
    path = f"/lab/{mine['id']}"
    corrected = "What it was compiled for has moved on"
    assert corrected not in shown(signed, path)

    bench = Bench(conn, alice, Inventory.load(TEST / "inventory.toml"))
    recommended: dict[str, JsonValue] = {"on": {"temperature": 0.2}}
    _ = correct_facts(bench, QWEN_MODEL, sampling={"recommended": recommended})
    page = shown(signed, path)
    assert corrected in page and ">Update<" in page
    page = shown(signed, f"/threads/{mine['id']}")
    assert corrected in page and f'action="/threads/{mine["id"]}/moved/follow"' in page

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
    path = f"/lab/{mine['id']}"

    greedy = thread(signed, "sampling", "greedy")["head"]["digest"]
    page = shown(signed, f"{path}?head={first}&sampling={greedy}")
    assert "Version 1 of 2" in page and "A newer version is saved" in page
    kept = urlencode({"sampling": greedy})
    assert f'href="?{kept}" data-head="{latest}"' in page
    assert variation_props(page)["look"]["head"]["id"] == first

    page = shown(signed, path)
    assert "Version 2 of 2" in page and "A newer version is saved" not in page
    assert f'href="?head={first}" data-head="{first}"' in page
    assert variation_props(page)["base"]["reasoning"] == off


@pytest.mark.slow
def test_a_variation_the_bench_refuses_is_a_page_of_its_own(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    archives = thread(signed, "configuration", LINES, "archive")
    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    path = f"/lab/{mine['id']}"
    for query, status, why in (
        (f"prompt={off}", 422, f"{off} isn&#39;t a stored chunk of prompt"),
        (f"head={archives['head']['id']}", 404, "no edit"),
        ("stack=x", 422, "query.stack: Extra inputs are not permitted"),
    ):
        got = signed.get(f"{path}?{query}")
        assert got.status_code == status, query
        assert got.headers["content-type"].startswith("text/html")
        assert why in got.text, (query, got.text[:2000])


@pytest.mark.slow
def test_the_runs_of_the_variation_are_on_its_page(signed: TestClient) -> None:
    runs = signed.get("/api/runs", params={"limit": 200}).json()
    configurations = signed.get(
        "/api/threads", params={"kind": "configuration", "owner": "alice"}
    ).json()
    heads = {c["head"]["digest"]: c for c in configurations}
    run = next(r for r in runs if r["skeleton"] in heads)
    page = shown(signed, f"/lab/{heads[run['skeleton']]['id']}")
    assert f'href="/runs/{run["id"]}"' in page
    assert run["id"] in {r["id"] for r in variation_props(page)["runs"]}


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
    assert f'href="/lab/{ran["id"]}"' in shown(signed, f"/runs/{run['id']}")

    off = thread(signed, "reasoning", OFF)["head"]["digest"]
    edits = f"/api/threads/{ran['id']}/edits"
    got = signed.post(
        edits, json={"head": ran["head"]["id"], "parts": {"reasoning": off}}
    )
    assert got.status_code == 201
    page = shown(signed, f"/runs/{run['id']}")
    assert f'href="/lab/{ran["id"]}?head={ran["head"]["id"]}"' in page
    assert "an earlier version" in page

    deleted = signed.patch(f"/api/threads/{ran['id']}", json={"deleted": True})
    assert deleted.status_code == 200
    archives = thread(signed, "configuration", ran["name"], "archive")
    page = shown(signed, f"/runs/{run['id']}")
    assert f'href="/lab/{archives["id"]}"' in page
