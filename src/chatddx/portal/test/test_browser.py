import re
import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path

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
from chatddx.test.world import LINES, QWEN, faked, world_facts

pytestmark = pytest.mark.slow


@pytest.fixture
def built() -> Path:
    found = settings.portal_assets()
    if not Assets(found).built:
        pytest.skip(f"nothing built in {found}: pnpm --dir frontend build")
    return found


@pytest.fixture
def served(db: str, built: Path, world: Inventory) -> FastAPI:
    return app(
        world, world_facts(), make_conninfo(settings.database(), dbname=db), built
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
        with page.expect_response(re.compile(r"/variation\?")):
            _ = page.select_option("#endpoint", QWEN)
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


def test_a_clinician_s_appendix_case_and_expectation_are_written_and_counted(
    page: Page,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    crlf = page.request.get("/api/families", params={"name": "crlf"}).json()[0]
    [expected] = page.request.get(f"/api/families/{crlf['id']}").json()["expectations"]
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
    assert page.request.delete(f"/api/threads/{mine['id']}").status == 204
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
