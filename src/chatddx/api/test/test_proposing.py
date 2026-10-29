import pytest
from fastapi.testclient import TestClient
from pydantic import JsonValue

from chatddx.api.test.helpers import thread
from chatddx.bench import Bench
from chatddx.bench.test.helpers import correct_facts
from chatddx.catalog import threads
from chatddx.store import People
from chatddx.test.world import LINES, QWEN_MODEL


def _moved(bench: Bench) -> int:
    found = People(bench.conn).find("archive")
    assert found is not None
    archive = Bench(bench.conn, found, bench.inventory)
    theirs = archive.thread(LINES, "configuration")[0].thread
    greedy = bench.thread("greedy", "sampling")[0].digest
    moved = archive.variation(theirs, {"sampling": greedy})
    head = threads.head(bench.rows, theirs).id
    return archive.edit(theirs, head, moved).edit.id


@pytest.mark.slow
def test_a_fork_is_updated_from_its_origin_once_it_has_moved_on(
    signed: TestClient, bench: Bench, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    proposal = f"/api/threads/{mine['id']}/proposal"
    update = f"/api/threads/{mine['id']}/update"
    assert signed.get(proposal).json() is None
    got = signed.post(update, json={"head": mine["head"]["id"]})
    assert (got.status_code, got.json()) == (
        422,
        {
            "detail": f"configuration {mine['id']} has nothing to update",
            "code": "refused",
        },
    )

    origin = _moved(bench)
    proposed = signed.get(proposal).json()
    assert proposed["reasons"] == ["origin"] and proposed["about"] == QWEN_MODEL
    assert proposed["origin_head"]["id"] == origin
    forked_from = signed.get(f"/api/threads/{mine['id']}").json()["forked_from"]
    assert proposed["base"]["id"] == forked_from
    assert proposed["varies"] == [] and proposed["component"] is None
    assert (proposed["clashes"], proposed["remodelled"], proposed["refused"]) == (
        [],
        None,
        None,
    )
    assert (
        proposed["recipe"]["sampling"] == bench.thread("greedy", "sampling")[0].digest
    )
    assert signed.get(proposal, headers=bob).status_code == 404

    stale = signed.post(update, json={"head": mine["head"]["id"] - 1})
    assert stale.status_code == 409
    got = signed.post(update, json={"head": mine["head"]["id"]})
    assert got.status_code == 201
    updated = got.json()
    assert (updated["digest"], updated["based_on"], updated["findings"]) == (
        proposed["digest"],
        origin,
        [],
    )
    assert signed.get(proposal).json() is None


@pytest.mark.slow
def test_a_configuration_is_updated_to_its_corrected_facts(
    signed: TestClient, bench: Bench, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    proposal = f"/api/threads/{mine['id']}/proposal"
    update = f"/api/threads/{mine['id']}/update"
    head = {"head": mine["head"]["id"]}

    recommended: dict[str, JsonValue] = {"on": {"temperature": 0.2}}
    _ = correct_facts(bench, QWEN_MODEL, sampling={"recommended": recommended})
    corrected = signed.get(proposal).json()
    assert (corrected["reasons"], corrected["about"]) == (["facts"], QWEN_MODEL)
    assert corrected["base"] is None and corrected["refused"] is None
    assert corrected["digest"] != mine["head"]["digest"]
    assert signed.get(proposal, headers=bob).status_code == 404

    assert signed.post(update, json={"head": head["head"] - 1}).status_code == 409
    got = signed.post(update, json={**head, "language": "sv"})
    assert (got.status_code, got.json()["detail"]) == (
        422,
        "a compiled configuration's language comes from its recipe",
    )
    got = signed.post(update, json=head)
    assert got.status_code == 201
    updated = got.json()
    assert (updated["digest"], updated["compilation"]) == (
        corrected["digest"],
        corrected["compilation"],
    )
    assert signed.get(proposal).json() is None
