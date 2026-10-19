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
from playwright.sync_api import Error, Page, expect, sync_playwright
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.app import app
from chatddx.portal.assets import Assets
from chatddx.portal.test.conftest import PASSWORD
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import GPT_OSS, LINES, LINES_GUIDED, QWEN, faked

pytestmark = pytest.mark.slow


def _settled(page: Page, run: str) -> None:
    for _ in range(1000):
        shown = page.request.get(f"/api/runs/{run}").json()
        if shown["finished"] and shown["job"]["status"] not in ("queued", "under way"):
            return
        time.sleep(0.02)
    raise AssertionError(f"run {run} is still under way")


def _endpoint(page: Page, name: str) -> dict[str, Any]:
    listed = page.request.get("/api/endpoints").json()
    [found] = [e for e in listed if e["name"] == name]
    return found


@pytest.fixture
def built() -> Path:
    found = settings.portal_assets()
    if not Assets(found).built:
        pytest.skip(f"nothing built in {found}: pnpm --dir frontend build")
    return found


@pytest.fixture
def served(db: str, built: Path, world: Inventory) -> FastAPI:
    return app(
        world,
        make_conninfo(settings.database(), dbname=db),
        built,
        worker=True,
    )


# localhost, as a browser keeps the __Host- session cookie over plain HTTP only there.
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
            browser = playwright.chromium.launch()
        except Error as e:
            pytest.skip(f"no browser for Playwright: {e.message.splitlines()[0]}")
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
        _ = page.goto(f"/configurations/{lines['id']}")
        expect(page.get_by_role("heading", name="Running it")).to_be_visible()
        # Accommodating for the test World: two endpoints serve Qwen3, so the page asks which.
        expect(page.get_by_text("Pick an endpoint to run it at.")).to_be_visible()
        _ = page.select_option("#endpoint", QWEN)
        expect(
            page.get_by_text(re.compile(rf"Sends \d+ items to {QWEN}"))
        ).to_be_visible()
        gpt_oss = _endpoint(page, GPT_OSS)["serves"]
        with page.expect_response(re.compile(r"/variation\?")):
            _ = page.select_option("#part-model", gpt_oss)
        expect(
            page.get_by_text(f"Sent to {GPT_OSS}, which serves its model.")
        ).to_be_visible()
        qwen = _endpoint(page, QWEN)["serves"]
        with page.expect_response(re.compile(r"/variation\?")):
            _ = page.select_option("#part-model", qwen)
        expect(page.get_by_text("Pick an endpoint to run it at.")).to_be_visible()
        _ = page.select_option("#endpoint", QWEN)
        expect(
            page.get_by_text(re.compile(rf"Sends \d+ items to {QWEN}"))
        ).to_be_visible()
        page.get_by_label("of the families picked").check()
        page.get_by_label("Find a family").fill("crlf")
        page.get_by_label("crlf", exact=True).check()
        expect(page.get_by_text("Sends 1 item to")).to_be_visible()
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

    _ = page.goto(f"/configurations/{configuration(LINES)}?tag=swedish")
    expect(
        page.get_by_text(
            "Left out: 3 cases in sv, as lines has no translations into sv."
        )
    ).to_be_visible()

    with faked(world, Store(conn).get):
        _ = page.goto(f"/configurations/{configuration(LINES_GUIDED)}?tag=swedish")
        expect(
            page.get_by_text(
                "A run per language: in en, 1 case; in sv, 3 cases, translated."
            )
        ).to_be_visible()
        expect(page.get_by_text("Left out")).to_have_count(0)
        _ = page.select_option("#endpoint", QWEN)
        expect(page.get_by_text("Sends 4 items to")).to_be_visible()
        page.get_by_role("button", name="Run it").click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        first = page.url.rsplit("/", 1)[1]
        other = page.get_by_role("link", name=re.compile(r", in sv$"))
        expect(other).to_be_visible()
        other.click()
        page.wait_for_url(re.compile(r"/runs/[0-9a-f-]{36}$"))
        expect(page.get_by_role("link", name=f"{first[:8]}, in en")).to_be_visible()

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
    _ = page.goto(f"/families/{crlf['id']}")
    written = page.locator(f'form[action="/families/{crlf["id"]}/appendices"]')
    written.locator('input[name="name"]').fill("ultrasound")
    written.locator("textarea").fill("Gallstones on ultrasound.")
    written.get_by_role("button", name="Write it").click()
    page.get_by_label("ultrasound").check()
    page.get_by_role("button", name="Build the case").click()
    expect(page.get_by_role("button", name="Write yours")).to_have_count(2)

    page.get_by_role("button", name="Write yours").first.click()
    page.get_by_role("button", name="+ pattern").first.click()
    page.get_by_label("pattern").first.fill("biliary & colic")
    expect(page.get_by_text("Nothing to say of it.")).to_be_visible()
    expect(page.get_by_text("a new thread of your own")).to_be_visible()
    page.get_by_role("button", name="Save").click()
    page.wait_for_url(re.compile(r"/threads/\d+$"))
    expect(page.get_by_role("heading", name="Change it")).to_be_visible()

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
        _ = page.get_by_label("Endpoint").select_option(QWEN)
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
    body = {"configuration": lines["id"], "endpoint": QWEN, "families": [crlf["id"]]}
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
    body = {"configuration": lines["id"], "endpoint": QWEN, "families": [noted["id"]]}
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
        written = page.get_by_role("form", name="A new judge")
        written.get_by_label("Name").fill("strict")
        _ = written.get_by_label("Asked at").select_option(QWEN)
        written.get_by_label("Seeds, a call each").fill("1, 2")
        written.get_by_role("button", name="Save the judge").click()
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


def test_what_a_judge_is_asked_is_rewritten_and_asked_through_a_judge_of_one_s_own(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    noted = page.request.get("/api/families", params={"name": "noted"}).json()[0]
    query: dict[str, str | float | bool] = {"kind": "scorer", "name": "judged"}
    judged = page.request.get("/api/threads", params=query).json()[0]
    was = page.request.get(f"/api/components/{judged['head']['digest']}").json()

    _ = page.goto(f"/review/{noted['id']}?scorer={judged['id']}")
    page.get_by_role("button", name=re.compile(r"^Compose judged")).click()
    composer = page.get_by_role("region", name="Composing a scorer")
    composer.get_by_role("button", name="Change what it is asked").first.click()
    panel = composer.get_by_role(
        "region", name="What its judge is asked, as you write it"
    )
    told = panel.get_by_label("What it is told to answer, text 1")
    expect(told).to_have_value(
        "Say whether the answer meets what was expected, and why."
    )
    told.fill("Say whether the answer meets carol's note, and why.")
    preview = panel.get_by_role("list", name="As it would read")
    expect(preview).to_contain_text("meets carol's note")
    expect(preview).to_contain_text("Chock, troligen septisk.")
    panel.get_by_role("button", name="Save what it is asked").click()
    expect(panel).to_have_count(0)
    composer.get_by_text("What its judge is asked").first.click()
    asked = composer.get_by_role("list", name="What its judge is asked").first
    expect(asked).to_contain_text("meets carol's note")
    composer.get_by_label("Name").fill("judged-anew")
    composer.get_by_role("button", name="Save").click()
    page.wait_for_url(lambda url: not url.endswith(f"scorer={judged['id']}"))

    query = {"kind": "judge", "name": "verdict", "owner": "alice"}
    [verdict] = page.request.get("/api/threads", params=query).json()
    held = page.request.get(f"/api/components/{verdict['head']['digest']}").json()
    query = {"kind": "configuration", "purpose": "judge", "owner": "alice"}
    judging = page.request.get("/api/threads", params=query).json()
    [asking] = [t for t in judging if t["name"] == "judge"]
    assert held["body"]["skeleton"] == asking["head"]["digest"]
    query = {"kind": "scorer", "name": "judged-anew"}
    [made] = page.request.get("/api/threads", params=query).json()
    now = page.request.get(f"/api/components/{made['head']['digest']}").json()
    old = {v["judge"] for v in was["body"]["views"] if v["metric"] == "verdict"}
    assert len(old) == 1 and old.isdisjoint(v["judge"] for v in now["body"]["views"])
    assert [v["judge"] for v in now["body"]["views"] if v["metric"] == "verdict"] == [
        verdict["head"]["digest"]
    ] * 2
    assert errors == []


def test_a_translator_carries_an_edited_instruction_over_and_saves_it(
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

    _ = page.goto(f"/translate/{guided['id']}?into=sv")
    expect(page.get_by_text("· 1 missing")).to_be_visible()
    page.get_by_role("button", name="Start from its translation").click()
    expect(
        page.get_by_text("Started from a similar text's translation")
    ).to_be_visible()
    swedish = page.get_by_label("Its translation").first
    expect(swedish).to_have_value(
        "Du bistår en läkare på en akutmottagning. Läs fallet och ge din bedömning."
    )
    swedish.fill(
        "Du bistår en läkare på en akutmottagning. Läs fallet och ge din bedömning "
        + "och plan."
    )
    expect(page.get_by_text("· every text translated")).to_be_visible()
    expect(page.get_by_text("Started from a similar text's translation")).to_have_count(
        0
    )
    request = page.get_by_role("group", name="Request")
    expect(request).to_contain_text("din bedömning och plan.")
    expect(
        page.get_by_text(
            re.compile(r"^Saves .*guided.*, and a new version of your lines-guided")
        )
    ).to_be_visible()
    with page.expect_navigation():
        page.get_by_role("button", name="Save").click()
    expect(page.get_by_text("· every text translated")).to_be_visible()
    expect(page.get_by_text(re.compile(r"^Not used by it: 1,"))).to_be_visible()

    look = page.request.get(
        f"/api/threads/{guided['id']}/variation", params={"tag": "swedish"}
    ).json()
    [swedish_cases] = [c for c in look["languages"] if c["language"] == "sv"]
    assert (swedish_cases["translated"], swedish_cases["refused"]) == (True, None)
    assert errors == []
