import pytest
from fastapi.testclient import TestClient
from pydantic import JsonValue

from chatddx.api.test.test_variations import thread
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
def test_a_fork_follows_its_origin_once_it_has_moved_on(
    signed: TestClient, bench: Bench, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    proposal, follows = (
        f"/api/threads/{mine['id']}/{to}" for to in ("proposal", "follows")
    )
    assert signed.get(proposal).json() is None
    got = signed.post(follows, json={"head": mine["head"]["id"]})
    assert (got.status_code, got.json()) == (
        422,
        {
            "detail": f"configuration {mine['id']} has nothing to follow",
            "code": "refused",
        },
    )

    origin = _moved(bench)
    proposed = signed.get(proposal).json()
    assert proposed["origin_head"]["id"] == origin
    forked_from = signed.get(f"/api/threads/{mine['id']}").json()["forked_from"]
    assert proposed["base"]["id"] == forked_from
    assert proposed["varies"] == [] and proposed["component"] is None
    assert (
        proposed["recipe"]["sampling"] == bench.thread("greedy", "sampling")[0].digest
    )
    assert signed.get(proposal, headers=bob).status_code == 404

    stale = signed.post(follows, json={"head": mine["head"]["id"] - 1})
    assert stale.status_code == 409
    got = signed.post(follows, json={"head": mine["head"]["id"]})
    assert got.status_code == 201
    followed = got.json()
    assert (followed["digest"], followed["based_on"], followed["findings"]) == (
        proposed["digest"],
        origin,
        [],
    )
    assert signed.get(proposal).json() is None


@pytest.mark.slow
def test_a_configuration_follows_its_corrected_facts(
    signed: TestClient, bench: Bench, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    facts, follows = (
        f"/api/threads/{mine['id']}/{to}" for to in ("moved", "moved/follows")
    )
    assert signed.get(facts).json() is None
    got = signed.post(follows, json={"head": mine["head"]["id"]})
    assert (got.status_code, got.json()) == (
        422,
        {
            "detail": f"configuration {mine['id']} was compiled for nothing that has "
            + "moved on",
            "code": "refused",
        },
    )

    recommended: dict[str, JsonValue] = {"on": {"temperature": 0.2}}
    moved = correct_facts(bench, QWEN_MODEL, sampling={"recommended": recommended})
    corrected = signed.get(facts).json()
    assert corrected["about"] == QWEN_MODEL and corrected["refused"] is None
    assert corrected["model"] is None and corrected["held"] is None
    assert (corrected["facts"]["id"], corrected["facts"]["digest"]) == (
        moved.id,
        moved.digest,
    )
    assert corrected["digest"] != mine["head"]["digest"]
    assert signed.get(facts, headers=bob).status_code == 404

    assert (
        signed.post(follows, json={"head": mine["head"]["id"] - 1}).status_code == 409
    )
    got = signed.post(follows, json={"head": mine["head"]["id"]})
    assert got.status_code == 201
    followed = got.json()
    assert (followed["digest"], followed["compilation"]) == (
        corrected["digest"],
        corrected["compilation"],
    )
    assert signed.get(facts).json() is None
