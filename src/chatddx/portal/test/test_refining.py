import re

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from chatddx.bench import Bench
from chatddx.factors.engine import FileDigest, LocalModel
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.portal.test.test_varying import thread
from chatddx.scripted.test.test_scripted_runs import held
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection
from chatddx.test.world import (
    COMPARED,
    GPT_OSS_ARTIFACT,
    JUDGE,
    LINES,
    LINES_GUIDED,
    LINES_INSTRUCTED,
    QWEN_ARTIFACT,
    QWEN_MODEL,
)


@pytest.fixture
def template(ran: str) -> str:
    return ran


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


@pytest.fixture
def bench(conn: Connection, alice: Person, world: Inventory) -> Bench:
    return Bench(conn, alice, world)


def said(page: str) -> str:
    main = page.split("<main", 1)[1]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", main))


@pytest.mark.slow
def test_refine_leads_to_one_s_first_configuration(signed: TestClient) -> None:
    got = signed.get("/refine")
    assert got.status_code == 303
    listed = signed.get(
        "/api/threads", params={"kind": "configuration", "owner": "alice"}
    ).json()
    first = min(listed, key=lambda t: t["name"] or t["title"])
    assert got.headers["location"] == f"/refine/{first['id']}"
    assert 'href="/refine"' in shown(signed, "/runs")


@pytest.mark.slow
def test_a_configuration_s_lineage_fares_side_by_side_on_a_set(
    signed: TestClient, bench: Bench
) -> None:
    mine = thread(signed, "configuration", LINES_INSTRUCTED)
    instructed, _, guided = (held(bench, name).run for name in COMPARED)
    page = shown(signed, f"/refine/{mine['id']}")
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
    page = shown(signed, f"/refine/{mine['id']}?by={by}")
    assert re.search(r"Lineage 4 \S+ — ", said(page))

    page = shown(signed, f"/refine/{mine['id']}?tag=targets")
    text = said(page)
    assert "not run" in text
    assert "None of them has a run at its model's latest engine yet." in text
    forced = said(shown(signed, f"/refine/{mine['id']}?model={GPT_OSS_ARTIFACT}"))
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
    text = said(shown(signed, f"/refine/{mine['id']}"))
    assert f"its model is behind {QWEN_ARTIFACT}: follow it" in text
    assert "None of them has a run at its model's latest engine yet." in text


@pytest.mark.slow
def test_what_isn_t_refined_here_isn_t_found(signed: TestClient) -> None:
    prompt = thread(signed, "prompt", "case")
    assert signed.get(f"/refine/{prompt['id']}").status_code == 404
    judge = signed.get(
        "/api/threads",
        params={"kind": "configuration", "purpose": "judge", "name": JUDGE},
    ).json()[0]
    got = signed.get(f"/refine/{judge['id']}")
    assert got.status_code == 404 and escape("a judge isn't run on cases") in got.text
    lines = thread(signed, "configuration", LINES)
    assert signed.get(f"/refine/{lines['id']}?model=nowhere").status_code == 422


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
