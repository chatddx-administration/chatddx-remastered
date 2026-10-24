import json
import re
import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from fastapi import FastAPI
from playwright.sync_api import Error, Page, Route, expect, sync_playwright

from chatddx import settings
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.locale import Locales
from chatddx.locale.test.helpers import catalog
from chatddx.portal.assets import Assets
from chatddx.portal.test.helpers import world_served
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.helpers import PASSWORD
from chatddx.test.world import (
    GPT_OSS_ARTIFACT,
    JUDGE,
    LINES,
    LINES_GUIDED,
    QWEN_ARTIFACT,
    faked,
)

__all__ = ["world_served"]

pytestmark = [pytest.mark.slow, pytest.mark.browser]


def _settled(page: Page, run: str) -> None:
    for _ in range(1000):
        shown = page.request.get(f"/api/runs/{run}").json()
        if shown["finished"] and shown["job"]["status"] not in ("queued", "under way"):
            return
        time.sleep(0.02)
    raise AssertionError(f"run {run} is still under way")


def _model(page: Page, name: str) -> dict[str, Any]:
    [found] = [m for m in page.request.get("/api/models").json() if m["name"] == name]
    return found


@pytest.fixture
def built() -> Path:
    found = settings.portal_assets()
    if not Assets(found).built:
        pytest.fail(f"nothing built in {found}: pnpm --dir frontend build")
    return found


# Accommodating for a browser, which keeps the __Host- session cookie over plain HTTP
# only on localhost.
@pytest.fixture
def portal(served: FastAPI) -> Iterator[str]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
    server = uvicorn.Server(
        uvicorn.Config(served, host="127.0.0.1", port=port, log_level="warning")
    )
    running = threading.Thread(target=server.run, daemon=True)
    running.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://localhost:{port}"
    server.should_exit = True
    running.join(5)


@pytest.fixture
def page(portal: str, alice: Person) -> Iterator[Page]:
    assert alice.login == "alice"
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(executable_path=settings.chromium())
        except Error as e:
            pytest.fail(f"no browser for Playwright: {e.message.splitlines()[0]}")
        opened = browser.new_page(base_url=portal)
        opened.set_default_timeout(15_000)
        _ = opened.goto("/sign-in")
        opened.fill('input[name="login"]', "alice")
        opened.fill('input[name="password"]', PASSWORD)
        opened.click("button:has-text('Sign in')")
        opened.wait_for_url(portal + "/")
        yield opened
        browser.close()


def test_a_variation_is_run_watched_halted_scored_again_and_run_again(
    page: Page,
    world: Inventory,
    conn: Connection,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    query: dict[str, str | float | bool] = {
        "kind": "configuration",
        "name": LINES,
        "owner": "alice",
    }
    lines = page.request.get("/api/threads", params=query).json()[0]

    with faked(world, Store(conn).get, delay=0.3):
        _ = page.goto(f"/lab/{lines['id']}")
        expect(page.get_by_role("heading", name="Running it")).to_be_visible()
        expect(page.get_by_text(f"Runs under {QWEN_ARTIFACT}.")).to_be_visible()
        expect(
            page.get_by_text(re.compile(rf"Sends \d+ items under {QWEN_ARTIFACT}"))
        ).to_be_visible()
        gpt_oss = _model(page, GPT_OSS_ARTIFACT)["weights"]
        with page.expect_response(re.compile(r"/variation\?")):
            _ = page.select_option("#part-model", gpt_oss)
        expect(page.get_by_text(f"Runs under {GPT_OSS_ARTIFACT}.")).to_be_visible()
        qwen = _model(page, QWEN_ARTIFACT)["weights"]
        with page.expect_response(re.compile(r"/variation\?")):
            _ = page.select_option("#part-model", qwen)
        expect(
            page.get_by_text(re.compile(rf"Sends \d+ items under {QWEN_ARTIFACT}"))
        ).to_be_visible()
        page.get_by_label("of the families picked").check()
        page.get_by_label("Find a family").fill("crlf")
        page.get_by_label("crlf", exact=True).check()
        expect(page.get_by_text("Sends 1 item under")).to_be_visible()
        page.get_by_role("button", name="Run it").click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        run = page.url.rsplit("/", 1)[1]

        expect(page.get_by_role("heading", name="Under way")).to_be_visible()
        expect(
            page.get_by_text(re.compile(r"(thinking|writing), \d+ tokens"))
        ).to_be_visible()
        page.get_by_role("button", name="Halt").click()
        expect(page.get_by_role("heading", name="Items")).to_be_visible()
        expect(page.get_by_text("Left to score by")).to_be_visible()

    with faked(world, Store(conn).get):
        page.get_by_role("button", name="Score again").click()
        expect(page.get_by_role("heading", name="Items")).to_be_visible()
        expect(page.get_by_text("Left to score by")).to_have_count(0)

        page.get_by_role("button", name="Run again").click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        assert page.url.rsplit("/", 1)[1] != run
        expect(page.get_by_role("heading", name="Items")).to_be_visible()
        expect(page.get_by_text("completed").first).to_be_visible()

    assert errors == []


def test_a_variation_says_where_it_runs_and_a_start_s_runs_link_each_other(
    page: Page,
    world: Inventory,
    conn: Connection,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def configuration(name: str) -> int:
        query: dict[str, str | float | bool] = {
            "kind": "configuration",
            "name": name,
            "owner": "alice",
        }
        return page.request.get("/api/threads", params=query).json()[0]["id"]

    _ = page.goto(f"/lab/{configuration(LINES)}?tag=swedish")
    expect(
        page.get_by_text(
            "Left out: 3 cases in Swedish, which lines has no translations into."
        )
    ).to_be_visible()

    with faked(world, Store(conn).get):
        _ = page.goto(f"/lab/{configuration(LINES_GUIDED)}?tag=swedish")
        expect(
            page.get_by_text(
                "A run per language: in English, 1 case; in Swedish, 3 cases, "
                + "translated."
            )
        ).to_be_visible()
        expect(page.get_by_text("Left out")).to_have_count(0)
        expect(page.get_by_text("Sends 4 items under")).to_be_visible()
        page.get_by_role("button", name="Run it").click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        first = page.url.rsplit("/", 1)[1]
        other = page.get_by_role("link", name=re.compile(r", in Swedish$"))
        expect(other).to_be_visible()
        other.click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        expect(page.get_by_role("link", name=f"{first[:8]}, in en")).to_be_visible()

    assert errors == []


def test_a_judge_s_lab_offers_no_run(page: Page) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    query: dict[str, str | float | bool] = {
        "kind": "configuration",
        "purpose": "judge",
        "name": JUDGE,
    }
    judge = page.request.get("/api/threads", params=query).json()[0]
    _ = page.goto(f"/lab/{judge['id']}")
    expect(page.get_by_role("heading", name="Saving it")).to_be_visible()
    expect(page.get_by_role("heading", name="Running it")).to_have_count(0)
    expect(page.get_by_role("heading", name="Its runs")).to_have_count(0)
    assert errors == []


def test_a_clinician_s_appendix_case_and_expectation_are_written_and_counted(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    crlf = page.request.get("/api/families", params={"name": "crlf"}).json()[0]
    [expected] = page.request.get(f"/api/families/{crlf['id']}").json()["cases"][0][
        "expectations"
    ]
    query: dict[str, str | float | bool] = {"kind": "expectation", "owner": "alice"}
    mine = next(
        t
        for t in page.request.get("/api/threads", params=query).json()
        if t["head"]["digest"] == expected["expectation"]
    )
    query = {"kind": "configuration", "name": LINES, "owner": "alice"}
    lines = page.request.get("/api/threads", params=query).json()[0]

    def missing() -> set[tuple[str, str]]:
        look = page.request.get(f"/api/threads/{lines['id']}/variation").json()
        return {
            (r["name"], r["label"]) for r in look["reach"] if crlf["id"] in r["missing"]
        }

    held = missing()
    deleted = {"deleted": True}
    path = f"/api/threads/{mine['id']}"
    assert page.request.patch(path, data=deleted).status == 200
    gone = missing()
    assert held < gone
    _ = page.goto("/library?kind=case")
    page.get_by_role("link", name="crlf", exact=True).click()
    page.get_by_role("link", name="A new appendix of its vignette").click()
    page.get_by_label("name", exact=True).fill("ultrasound")
    page.get_by_label("text", exact=True).fill("Gallstones on ultrasound.")
    page.get_by_role("button", name="Write it").click()
    page.wait_for_url(re.compile(r"/threads/\d+$"))
    _ = page.goto(f"/cases/{crlf['id']}")
    _ = page.get_by_label("appendix 1").select_option(label="ultrasound")
    page.get_by_role("button", name="Build it").click()
    expect(page.get_by_role("link", name="write yours")).to_have_count(2)

    page.get_by_role("link", name="write yours").first.click()
    page.get_by_label("name", exact=True).fill("mine again")
    page.get_by_role("button", name="Write it as JSON").click()
    page.get_by_label("data", exact=True).fill(json.dumps(expected["data"]))
    page.get_by_role("button", name="Write it").click()
    page.wait_for_url(re.compile(r"/threads/\d+$"))
    expect(page.get_by_role("button", name="Save it")).to_be_visible()

    written_now = missing()
    assert held <= written_now < gone
    assert errors == []


def test_a_clinician_reviews_a_case_and_its_views_read_what_is_typed(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    noted = page.request.get("/api/families", params={"name": "noted"}).json()[0]
    query: dict[str, str | float | bool] = {"kind": "scorer", "name": "judged"}
    judged = page.request.get("/api/threads", params=query).json()[0]
    vignette = page.request.get(f"/api/families/{noted['id']}/vignette").json()

    _ = page.goto(f"/review/{noted['id']}?scorer={judged['id']}")
    first = vignette["text"].strip().splitlines()[0]
    expect(page.locator("#review-vignette")).to_contain_text(first)
    page.set_viewport_size({"width": 1440, "height": 900})
    for drawer in page.locator("details[data-drawer]").all():
        drawer.locator("summary").first.click()
    expect(page.locator("details[data-drawer][open]")).to_have_count(2)
    assert page.evaluate("document.documentElement.scrollHeight") == 900
    notes = page.get_by_role("list", name="What reads notes")
    expect(notes).to_contain_text("Chock, troligen septisk.")
    expect(page.get_by_text("Nothing to save: it holds this already.")).to_be_visible()
    page.get_by_label("comment").first.fill("Septisk chock: odla, ge antibiotika.")
    expect(notes).to_contain_text("Septisk chock: odla, ge antibiotika.")
    diagnosis = page.get_by_role("list", name="What reads diagnosis")
    page.get_by_label("pattern").first.fill("septic & shock")
    expect(diagnosis).to_contain_text("pattern: septic & shock")
    expect(page.get_by_text("Saves a new version of it.")).to_be_visible()
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_text(re.compile(r"^Version 2 of 2, "))).to_be_visible()
    expect(page.get_by_label("pattern").first).to_have_value("septic & shock")

    page.get_by_text("Add to it: an appendix, or a case of several").click()
    page.get_by_label("Name").fill("ultrasound")
    page.get_by_label("Text, as it is added to the vignette").fill("Free fluid.")
    page.get_by_role("button", name="Write the appendix").click()
    page.get_by_text("Add to it: an appendix, or a case of several").click()
    page.get_by_label("ultrasound").check()
    page.get_by_role("button", name="Build the case").click()
    page.wait_for_url(re.compile(r"[?&]case=sha256"))
    expect(page.get_by_text("Free fluid.")).to_be_visible()
    expect(page.get_by_text("a new thread of your own")).to_be_visible()
    expect(page.get_by_label("pattern").first).to_have_value("septic & shock")

    page.locator("body").press("j")
    page.wait_for_url(lambda url: f"/review/{noted['id']}" not in url)
    assert errors == []


def test_a_case_with_none_of_one_s_own_shows_the_shared_one_and_waits_for_typing(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    crlf = page.request.get("/api/families", params={"name": "crlf"}).json()[0]
    [expected] = page.request.get(f"/api/families/{crlf['id']}").json()["cases"][0][
        "expectations"
    ]
    query: dict[str, str | float | bool] = {"kind": "expectation", "owner": "alice"}
    mine = next(
        t
        for t in page.request.get("/api/threads", params=query).json()
        if t["head"]["digest"] == expected["expectation"]
    )
    path = f"/api/threads/{mine['id']}"
    assert page.request.patch(path, data={"deleted": True}).status == 200

    with page.expect_response(lambda r: r.url.endswith("/api/components/check")):
        _ = page.goto(f"/review/{crlf['id']}")
    expect(page.get_by_role("button", name="Save")).to_be_enabled()
    pattern = expected["data"]["diagnosis"]["pattern"]
    expect(page.locator("[data-offered]")).to_contain_text(pattern)
    expect(page.get_by_text("a new thread of your own")).to_be_visible()
    expect(page.get_by_text("Nothing to say of it.")).to_have_count(0)
    expect(page.get_by_text("expectation.invalid")).to_have_count(0)
    page.get_by_role("button", name="+ pattern").first.click()
    page.get_by_label("pattern").first.fill(pattern)
    expect(page.get_by_text("Nothing to say of it.")).to_be_visible()
    assert errors == []


def test_a_case_is_run_from_its_review_and_its_answer_read_in_the_record(
    page: Page,
    world: Inventory,
    conn: Connection,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    crlf = page.request.get("/api/families", params={"name": "crlf"}).json()[0]
    query: dict[str, str | float | bool] = {
        "kind": "configuration",
        "name": LINES,
        "owner": "alice",
    }
    lines = page.request.get("/api/threads", params=query).json()[0]

    with faked(world, Store(conn).get, delay=0.05):
        _ = page.goto(f"/review/{crlf['id']}")
        record = page.locator('details[data-drawer="record"]')
        expect(record).to_contain_text("Record")
        record.locator("summary").first.click()
        _ = page.get_by_label("Configuration").select_option(str(lines["id"]))
        _ = page.get_by_label("Model").select_option(QWEN_ARTIFACT)
        page.get_by_role("button", name="Run it").click()
        expect(record).to_have_attribute("open", "")
        page.wait_for_url(re.compile(rf"/review/{crlf['id']}$"))
        assert page.evaluate("window.scrollY") == 0
        pending = record.locator("[data-pending]")
        expect(pending).to_contain_text(re.compile(r"queued|ended|scoring|done"))
        answer = record.locator("details[data-answer] summary")
        expect(answer).to_have_count(1, timeout=30_000)
    expect(page.locator("[data-pending]")).to_have_count(0)
    answer.click()
    [run] = page.request.get("/api/runs", params={"reaching": crlf["case"]}).json()
    [item] = page.request.get(
        f"/api/runs/{run['id']}/items", params={"case": crlf["case"]}
    ).json()
    said = item["answer"]["value"].strip().splitlines()[0]
    expect(record.locator("[data-answer-body]")).to_contain_text(said)
    assert errors == []


def test_a_scorer_is_composed_beside_the_case_and_tried_on_its_answers_as_typed(
    page: Page,
    world: Inventory,
    conn: Connection,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    crlf = page.request.get("/api/families", params={"name": "crlf"}).json()[0]
    query: dict[str, str | float | bool] = {
        "kind": "configuration",
        "name": LINES,
        "owner": "alice",
    }
    lines = page.request.get("/api/threads", params=query).json()[0]
    body = {"configuration": lines["id"], "families": [crlf["id"]]}
    with faked(world, Store(conn).get):
        started = page.request.post("/api/runs", data=body).json()
        run = started["runs"][0]["run"]
        _settled(page, run)
    [item] = page.request.get(
        f"/api/runs/{run}/items", params={"case": crlf["case"]}
    ).json()
    first = item["answer"]["value"].strip().splitlines()[0]
    word = re.findall(r"[A-Za-z]{3,}", first)[0].lower()
    query = {"kind": "scorer", "name": LINES}
    scorer = page.request.get("/api/threads", params=query).json()[0]

    _ = page.goto(f"/review/{crlf['id']}?scorer={scorer['id']}")
    page.get_by_role("button", name=re.compile(rf"^Compose {LINES}")).click()
    composer = page.get_by_role("region", name="Composing a scorer")
    differential = composer.locator("li").nth(1)
    expect(differential.get_by_label("Its label")).to_have_value("differential")
    page.get_by_label("pattern").first.fill(word)
    expect(differential.get_by_label("Tried on your answers")).to_contain_text("1.00")
    page.get_by_label("pattern").first.fill("nothing & like & it")
    expect(differential.get_by_label("Tried on your answers")).to_contain_text("0.00")

    composer.get_by_role("button", name="Start a new one").click()
    composer.get_by_label("Its label").fill("named")
    _ = composer.get_by_label("Reads of what is expected").select_option(
        label="diagnosis"
    )
    composer.get_by_label("line by line, as a list").check()
    _ = composer.get_by_label("Compared by").select_option("mentions")
    page.get_by_label("pattern").first.fill(word)
    expect(composer.get_by_label("Tried on your answers")).to_contain_text("1.00")
    expect(page.get_by_role("list", name="What reads diagnosis")).to_contain_text(
        "named"
    )
    composer.get_by_label("Name").fill("mine")
    composer.get_by_role("button", name="Save").click()
    page.wait_for_url(lambda url: not url.endswith(f"scorer={scorer['id']}"))
    mine = page.request.get("/api/threads", params={"kind": "scorer", "name": "mine"})
    [made] = mine.json()
    assert page.url.endswith(f"scorer={made['id']}")
    edits = page.request.get(f"/api/threads/{made['id']}/edits").json()
    assert edits[-1]["labels"]["views"] == ["named"]
    expect(page.get_by_role("navigation", name="Scorers")).to_contain_text("mine")
    assert errors == []


def test_a_scorer_s_page_fits_a_phone(page: Page) -> None:
    query: dict[str, str | float | bool] = {"kind": "scorer", "name": LINES}
    lines = page.request.get("/api/threads", params=query).json()[0]
    page.set_viewport_size({"width": 390, "height": 844})
    _ = page.goto(f"/scoring/{lines['id']}")
    expect(page.get_by_role("heading", name="Its views")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth") == 390


def test_a_judged_view_is_composed_with_a_new_judge_and_scored_through_the_worker(
    page: Page,
    world: Inventory,
    conn: Connection,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    noted = page.request.get("/api/families", params={"name": "noted"}).json()[0]
    query: dict[str, str | float | bool] = {
        "kind": "configuration",
        "name": LINES,
        "owner": "alice",
    }
    lines = page.request.get("/api/threads", params=query).json()[0]
    body = {"configuration": lines["id"], "families": [noted["id"]]}
    query = {"kind": "scorer", "name": LINES}
    scorer = page.request.get("/api/threads", params=query).json()[0]

    with faked(world, Store(conn).get):
        run = page.request.post("/api/runs", data=body).json()["runs"][0]["run"]
        _settled(page, run)
        _ = page.goto(f"/review/{noted['id']}?scorer={scorer['id']}")
        page.get_by_role("button", name=re.compile(rf"^Compose {LINES}")).click()
        composer = page.get_by_role("region", name="Composing a scorer")
        composer.get_by_role("button", name="Start a new one").click()
        composer.get_by_label("Its label").fill("met")
        _ = composer.get_by_label("Reads of what is expected").select_option(
            label="notes where author is carol › comment"
        )
        _ = composer.get_by_role("combobox", name="Compared by").select_option(
            "verdict"
        )
        judge = composer.get_by_role("combobox", name="Judge")
        _ = judge.select_option("new")
        written = page.get_by_role("region", name="A new judge")
        written.get_by_label("Name").fill("strict")
        _ = written.get_by_label("Asked under the model").select_option(QWEN_ARTIFACT)
        written.get_by_label("Seeds, a call each").fill("1, 2")
        written.get_by_role("button", name="Save").click()
        expect(written).to_have_count(0)
        expect(judge.locator("option:checked")).to_contain_text("strict")
        expect(composer.get_by_role("combobox", name="Its verdict at")).to_have_value(
            "/meets"
        )
        composer.get_by_text("What its judge is asked").click()
        asked = composer.get_by_role("list", name="What its judge is asked")
        expect(asked).to_contain_text("Chock, troligen septisk.")
        expect(asked).to_contain_text("‹completion›")
        expect(composer.get_by_label("Tried on your answers")).to_contain_text("judged")
        composer.get_by_label("Name").fill("noted-judged")
        composer.get_by_role("button", name="Save").click()
        page.wait_for_url(lambda url: not url.endswith(f"scorer={scorer['id']}"))

        record = page.locator('details[data-drawer="record"]')
        if record.get_attribute("open") is None:
            record.locator("summary").first.click()
        record.get_by_role("button", name="Score again").click()
        expect(page.locator("[data-pending]")).to_have_count(0, timeout=30_000)
    expect(record).not_to_contain_text("to score")
    query = {"kind": "judge", "name": "strict"}
    [strict] = page.request.get("/api/threads", params=query).json()
    held = page.request.get(f"/api/components/{strict['head']['digest']}").json()
    assert held["body"]["seeds"] == [1, 2]
    assert errors == []


def test_what_a_judge_is_asked_is_rewritten_on_its_page_and_picked_in_review(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    noted = page.request.get("/api/families", params={"name": "noted"}).json()[0]
    query: dict[str, str | float | bool] = {"kind": "judge", "name": "verdict"}
    [archives] = page.request.get("/api/threads", params=query).json()
    query = {"kind": "scorer", "name": "judged"}
    judged = page.request.get("/api/threads", params=query).json()[0]
    was = page.request.get(f"/api/components/{judged['head']['digest']}").json()

    _ = page.goto(f"/scoring/{archives['id']}")
    page.get_by_role("button", name="Change what it is asked").click()
    panel = page.get_by_role("region", name="What its judge is asked, as you write it")
    told = panel.get_by_label("What it is told to answer, text 1")
    expect(told).to_have_value(
        "Say whether the answer meets what was expected, and why."
    )
    told.fill("Say whether the answer meets carol's note, and why.")
    preview = panel.get_by_role("list", name="As it would read")
    expect(preview).to_contain_text("meets carol's note")
    expect(preview).to_contain_text("Chock, troligen septisk.")
    panel.get_by_role("button", name="Save what it is asked").click()
    page.wait_for_url(lambda url: not url.endswith(f"/scoring/{archives['id']}"))

    query = {"kind": "judge", "name": "verdict", "owner": "alice"}
    [verdict] = page.request.get("/api/threads", params=query).json()
    assert page.url.endswith(f"/scoring/{verdict['id']}")
    asked = page.get_by_role("region", name="What it is asked", exact=True)
    expect(asked).to_contain_text("meets carol's note")
    held = page.request.get(f"/api/components/{verdict['head']['digest']}").json()
    query = {"kind": "configuration", "purpose": "judge", "owner": "alice"}
    judging = page.request.get("/api/threads", params=query).json()
    [asking] = [t for t in judging if t["name"] == "judge"]
    assert held["body"]["skeleton"] == asking["head"]["digest"]
    query = {"kind": "scorer", "name": "judged"}
    [still] = page.request.get("/api/threads", params=query).json()
    assert still["head"]["digest"] == judged["head"]["digest"]

    _ = page.goto(f"/review/{noted['id']}?scorer={judged['id']}")
    page.get_by_role("button", name=re.compile(r"^Compose judged")).click()
    composer = page.get_by_role("region", name="Composing a scorer")
    expect(composer.get_by_text("Change what it is asked")).to_have_count(0)
    picks = composer.get_by_role("combobox", name="Judge", exact=True)
    for at in range(2):
        _ = picks.nth(at).select_option(verdict["head"]["digest"])
    changing = composer.get_by_role(
        "link", name="What it is asked is changed on Scoring"
    )
    expect(changing.first).to_have_attribute("href", f"/scoring/{verdict['id']}")
    composer.get_by_label("Name").fill("judged-anew")
    composer.get_by_role("button", name="Save").click()
    page.wait_for_url(lambda url: not url.endswith(f"scorer={judged['id']}"))

    query = {"kind": "scorer", "name": "judged-anew"}
    [made] = page.request.get("/api/threads", params=query).json()
    now = page.request.get(f"/api/components/{made['head']['digest']}").json()
    old = {v["judge"] for v in was["body"]["views"] if v["metric"] == "verdict"}
    assert len(old) == 1 and old.isdisjoint(v["judge"] for v in now["body"]["views"])
    assert [v["judge"] for v in now["body"]["views"] if v["metric"] == "verdict"] == [
        verdict["head"]["digest"]
    ] * 2
    assert errors == []


def test_a_translator_carries_an_edited_instruction_over_and_the_lab_takes_it(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def thread(kind: str, name: str) -> dict[str, Any]:
        query: dict[str, str | float | bool] = {
            "kind": kind,
            "name": name,
            "owner": "alice",
        }
        return page.request.get("/api/threads", params=query).json()[0]

    clinician = thread("instructions", "clinician")
    body = page.request.get(f"/api/components/{clinician['head']['digest']}").json()
    text = body["body"]["text"]
    text[0] = text[0].replace("your assessment.", "your assessment and plan.")
    changed = {"head": clinician["head"]["id"], "component": body["body"]}
    edited = page.request.post(
        f"/api/threads/{clinician['id']}/edits", data={**changed, "language": "en"}
    )
    assert edited.status == 201, edited.json()
    guided = thread("configuration", LINES_GUIDED)
    parts = {"instructions": edited.json()["digest"]}
    moved = page.request.post(
        f"/api/threads/{guided['id']}/edits",
        data={"head": guided["head"]["id"], "parts": parts},
    )
    assert moved.status == 201, moved.json()

    held: dict[str, str | float | bool] = {"kind": "translations", "owner": "alice"}
    [translations] = page.request.get("/api/threads", params=held).json()
    _ = page.goto(f"/threads/{translations['id']}?into=sv")
    expect(
        page.get_by_text(re.compile("started from the translation of a similar text"))
    ).to_be_visible()
    swedish = page.get_by_label("Its translation").first
    expect(swedish).to_have_value(
        "Du bistår en läkare på en akutmottagning. Läs fallet och ge din bedömning."
    )
    swedish.fill(
        "Du bistår en läkare på en akutmottagning. Läs fallet och ge din bedömning "
        + "och plan."
    )
    with page.expect_navigation():
        page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Not translated yet")).to_have_count(0)

    page.locator(f'a[href^="/lab/{guided["id"]}?translations="]').click()
    page.wait_for_url(re.compile(rf"/lab/{guided['id']}\?translations="))
    expect(
        page.get_by_text(re.compile(r"^Saves version \d+ of this configuration"))
    ).to_be_visible()
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()

    look = page.request.get(
        f"/api/threads/{guided['id']}/variation", params={"tag": "swedish"}
    ).json()
    [swedish_cases] = [c for c in look["languages"] if c["language"] == "sv"]
    assert (swedish_cases["translated"], swedish_cases["refused"]) == (True, None)
    assert errors == []


def test_a_text_an_expectation_and_a_scorer_s_views_are_written_in_their_editors(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def mine(kind: str, name: str | None = None) -> dict[str, Any]:
        query: dict[str, str | float | bool] = {"kind": kind, "owner": "alice"}
        listed = page.request.get("/api/threads", params=query).json()
        return next(t for t in listed if name in (None, t["name"]))

    def body(thread: dict[str, Any]) -> dict[str, Any]:
        head = page.request.get(f"/api/threads/{thread['id']}").json()["head"]
        return page.request.get(f"/api/components/{head['digest']}").json()["body"]

    clinician = mine("instructions", "clinician")
    _ = page.goto(f"/threads/{clinician['id']}")
    expect(page.get_by_text("‹what it is told to answer›")).to_be_visible()
    page.get_by_label("text, text 1").fill("Be brief.")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    [text, insert] = body(clinician)["text"]
    assert (text, insert["insert"]) == ("Be brief.", "output_guidance")

    expectation = mine("expectation")
    was = body(expectation)
    _ = page.goto(f"/threads/{expectation['id']}")
    diagnosis = page.get_by_role("group", name="diagnosis", exact=True)
    diagnosis.get_by_label("pattern", exact=True).fill("pneumonitis")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    now = body(expectation)
    assert now["data"]["diagnosis"]["pattern"] == "pneumonitis"
    assert (now["case"], now["expectation_schema"]) == (
        was["case"],
        was["expectation_schema"],
    )

    _ = page.goto("/library/new?kind=expectation")
    expect(page.get_by_text("Pick its expectation schema first")).to_be_visible()
    _ = page.get_by_label("expectation schema", exact=True).select_option(index=1)
    expect(page.get_by_role("group", name="diagnosis", exact=True)).to_be_visible()
    page.get_by_role("button", name="Write it as JSON").click()
    expect(page.get_by_label("data", exact=True)).to_be_visible()
    page.get_by_role("button", name="Back to the form").click()
    expect(page.get_by_role("group", name="diagnosis", exact=True)).to_be_visible()

    query: dict[str, str | float | bool] = {"kind": "scorer", "name": "lines"}
    [lines] = page.request.get("/api/threads", params=query).json()
    forks = f"/api/threads/{lines['id']}/forks"
    scorer = page.request.post(forks, data={"name": "my lines"}).json()
    _ = page.goto(f"/threads/{scorer['id']}")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 1 of 1")).to_be_visible()
    edits = f"/api/threads/{scorer['id']}/edits"
    assert len(page.request.get(edits).json()) == 1
    page.get_by_label("Its label").first.fill("first")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    assert page.request.get(edits).json()[-1]["labels"]["views"][0] == "first"
    assert body(scorer)["views"] == body(lines)["views"]
    assert errors == []


def test_few_shot_messages_and_a_contract_are_written_in_forms_and_json_checked_as_typed(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def mine(kind: str, name: str) -> dict[str, Any]:
        query: dict[str, str | float | bool] = {"kind": kind, "owner": "alice"}
        listed = page.request.get("/api/threads", params=query).json()
        return next(t for t in listed if t["name"] == name)

    def body(thread: dict[str, Any]) -> dict[str, Any]:
        head = page.request.get(f"/api/threads/{thread['id']}").json()["head"]
        return page.request.get(f"/api/components/{head['digest']}").json()["body"]

    worked = mine("few_shot", "worked-example")
    was = body(worked)["messages"]
    _ = page.goto(f"/threads/{worked['id']}")
    page.get_by_role("button", name="+ messages").click()
    added = page.get_by_role("group", name=f"messages {len(was) + 1}", exact=True)
    _ = added.get_by_label("role", exact=True).select_option(label="user")
    added.get_by_label("content", exact=True).fill("And now?")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    assert body(worked)["messages"] == [*was, {"role": "user", "content": "And now?"}]

    native = mine("output", "native")
    _ = page.goto(f"/threads/{native['id']}")
    _ = page.get_by_label("kind", exact=True).select_option("tool")
    page.get_by_label("name", exact=True).fill("final_result")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    assert body(native)["contract"]["kind"] == "tool"
    assert body(native)["contract"]["name"] == "final_result"

    off = mine("reasoning", "off")
    _ = page.goto(f"/threads/{off['id']}")
    kwargs = page.get_by_label("chat template kwargs", exact=True)
    kwargs.fill('{"enable_thinking": fals')
    expect(page.get_by_text("It isn't JSON yet")).to_be_visible()
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 1 of 1")).to_be_visible()
    assert len(page.request.get(f"/api/threads/{off['id']}/edits").json()) == 1
    kwargs.fill('{"enable_thinking": false}')
    expect(page.get_by_text("It isn't JSON yet")).to_be_hidden()
    _ = page.get_by_label("level", exact=True).select_option(label="none")
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    assert body(off)["chat_template_kwargs"] == {"enable_thinking": False}
    assert errors == []


def test_a_researcher_s_chunks_are_written_in_their_forms_and_made_into_a_configuration(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def mine(kind: str, name: str) -> dict[str, Any]:
        query: dict[str, str | float | bool] = {"kind": kind, "name": name}
        listed = page.request.get("/api/threads", params={**query, "owner": "alice"})
        return listed.json()[0]

    case = mine("prompt", "case")
    _ = page.goto(f"/threads/{case['id']}")
    segments = ["The case:\n", {"slot": "vignette"}, {"slot": "appendices"}]
    page.get_by_role("button", name="Write it as JSON").click()
    page.get_by_label("segments", exact=True).fill(json.dumps(segments))
    page.get_by_role("button", name="Save it").click()
    expect(page.get_by_text("Version 2 of 2")).to_be_visible()
    prompt = mine("prompt", "case")["head"]["digest"]
    held = page.request.get(f"/api/components/{prompt}").json()["body"]
    assert held["segments"] == [
        "The case:\n",
        {"slot": "vignette"},
        {"slot": "appendices"},
    ]

    _ = page.goto("/library?kind=sampling")
    page.get_by_role("link", name="Write a new one").click()
    page.get_by_label("temperature", exact=True).fill("0.3")
    page.get_by_label("name", exact=True).fill("warm")
    page.get_by_role("button", name="Write it").click()
    page.wait_for_url(re.compile(r"/threads/\d+$"))
    warm = mine("sampling", "warm")["head"]["digest"]
    assert (
        page.request.get(f"/api/components/{warm}").json()["body"]["temperature"] == 0.3
    )

    _ = page.goto("/library?kind=configuration")
    page.get_by_role("link", name="Write a new one").click()
    _ = page.get_by_label("prompt", exact=True).select_option(prompt)
    _ = page.get_by_label("output", exact=True).select_option(label=LINES)
    _ = page.get_by_label("sampling", exact=True).select_option(warm)
    model = _model(page, QWEN_ARTIFACT)["weights"]
    _ = page.get_by_label("model", exact=True).select_option(model)
    page.get_by_label("name", exact=True).fill("lines-warm")
    page.get_by_role("button", name="Write it").click()
    page.wait_for_url(re.compile(r"/threads/\d+$"))
    configuration = mine("configuration", "lines-warm")
    recipe = page.request.get(f"/api/threads/{configuration['id']}").json()["recipe"]
    assert (recipe["prompt"], recipe["sampling"]) == (prompt, warm)
    assert errors == []


def test_a_trial_is_begun_of_the_picked_cases_in_their_language_and_run(
    page: Page,
    world: Inventory,
    conn: Connection,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    _ = page.goto("/library?kind=case")
    page.get_by_label("pick nfd").check()
    page.get_by_label("pick svenska").check()
    page.get_by_role("button", name="Begin a trial of the picked").click()
    page.wait_for_url(re.compile(r"/library/new\?"))
    page.get_by_label("name", exact=True).fill("swedish")
    _ = page.get_by_label("skeleton").select_option(label=LINES_GUIDED)
    _ = page.get_by_label("engine").select_option(label=QWEN_ARTIFACT)
    page.get_by_role("button", name="Write it").click()
    page.wait_for_url(re.compile(r"/threads/\d+$"))
    expect(page.get_by_label("skeleton")).to_have_text(
        re.compile(f"{LINES_GUIDED}, in Swedish")
    )

    page.get_by_role("link", name="Run it").click()
    page.wait_for_url(re.compile(r"/lab/run\?"))
    page.get_by_label("Score it once it is done").uncheck()
    with faked(world, Store(conn).get):
        page.get_by_role("button", name="Run it").click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        expect(page.get_by_role("link", name="swedish")).to_be_visible()
    assert errors == []


# Accommodating for Chromium, which runs no script on a page while a navigation from it is held:
# the navigations a press starts are cancelled instead, which leaves the page as pressed.
def test_a_press_shows_until_the_next_page_comes_and_sends_its_form_once(
    page: Page,
) -> None:
    asked: list[str] = []
    held: list[Route] = []

    def cancelled(route: Route) -> None:
        asked.append(route.request.url)
        route.abort("aborted")

    back = "dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))"
    stop = "setTimeout(() => document.querySelector('[value=trial]').click()); setTimeout(stop, 200)"
    new = re.compile(r"/library/new\?")
    marked = page.locator("html[data-leaving], [data-pressed], [data-sent]")
    _ = page.goto("/library?kind=case")
    page.get_by_label("pick nfd").check()
    _ = page.route(new, cancelled)
    begin = page.get_by_role("button", name="Begin a trial of the picked")
    begin.click()
    expect(begin).to_have_attribute("data-pressed", "")
    expect(page.locator("html")).to_have_attribute("data-leaving", "")
    begin.click()
    page.wait_for_timeout(100)
    assert len(asked) == 1 and "kind=trial" in asked[0]

    _ = page.evaluate(back)
    expect(marked).to_have_count(0)
    begin.click()
    expect(begin).to_have_attribute("data-pressed", "")
    page.wait_for_timeout(100)
    assert len(asked) == 2

    page.unroute(new)
    _ = page.route(new, lambda r: held.append(r))
    _ = page.evaluate(back)
    _ = page.evaluate(stop)
    page.wait_for_timeout(400)
    assert len(held) == 1
    expect(marked).to_have_count(0)
    held.pop().abort()

    _ = page.goto("/library?kind=configuration")
    _ = page.route(re.compile(r"/threads/\d+$"), cancelled)
    lines = page.get_by_role("link", name=LINES, exact=True).first
    lines.click()
    expect(lines).to_have_attribute("data-pressed", "")
    expect(page.locator("html")).to_have_attribute("data-leaving", "")


def test_a_case_over_the_limit_isn_t_sent_and_says_why(
    page: Page, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "TYPED_TEXT_LIMIT", 10)
    _ = page.goto("/")
    case = page.get_by_label("The case")
    over = page.get_by_text(re.compile(r"^A case holds at most 10 characters"))
    case.fill("chest pai\N{ANATOMICAL HEART}")
    expect(over).to_have_count(0)
    case.fill("chest pain\N{ANATOMICAL HEART}")
    expect(over).to_have_text("A case holds at most 10 characters; this one has 11.")
    expect(page.get_by_role("button", name="Analyze")).to_be_disabled()


def test_an_island_says_what_its_page_s_catalog_holds_in_the_locale_asked_for(
    page: Page, served: FastAPI, tmp_path: Path
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    served.state.locales = Locales(
        catalog(
            tmp_path,
            """
            #: frontend/src/islands/Home.svelte
            msgid "Analyze"
            msgstr "Analysera"

            #: frontend/src/islands/Home.svelte
            msgid ""
            "<span class=\\"gradient-text\\">Emergency</span> <span "
            "class=\\"text-foreground\\">Differential Diagnostics</span>"
            msgstr "<span class=\\"gradient-text\\">Akut</span> differentialdiagnostik"

            #: frontend/src/islands/Variation.svelte
            msgid "Sends %(items)s under %(model)s, one at a time."
            msgstr "Skickar %(items)s under %(model)s, en i taget."

            #: frontend/src/islands/Variation.svelte
            msgid "%(n)s item"
            msgid_plural "%(n)s items"
            msgstr[0] "%(n)s post"
            msgstr[1] "%(n)s poster"
            """,
        )
    )
    page.set_extra_http_headers({"accept-language": "sv"})
    _ = page.goto("/")
    expect(
        page.get_by_role("heading", name="Akut differentialdiagnostik")
    ).to_be_visible()
    expect(page.get_by_role("button", name="Analysera")).to_be_visible()
    expect(page.get_by_text("Written in")).to_be_visible()

    query: dict[str, str | float | bool] = {
        "kind": "configuration",
        "name": LINES,
        "owner": "alice",
    }
    lines = page.request.get("/api/threads", params=query).json()[0]
    _ = page.goto(f"/lab/{lines['id']}")
    expect(
        page.get_by_text(
            re.compile(rf"Skickar \d+ poster under {QWEN_ARTIFACT}, en i taget\.")
        )
    ).to_be_visible()
    assert errors == []
