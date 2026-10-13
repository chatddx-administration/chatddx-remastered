import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.test_variations import thread
from chatddx.bench import Bench
from chatddx.store import People
from chatddx.test.world import LINES, QWEN

pytestmark = pytest.mark.solidified


def _moved(bench: Bench) -> int:
    found = People(bench.conn).find("archive")
    assert found is not None
    archive = Bench(bench.conn, found, bench.inventory, bench.facts)
    theirs = archive.thread("configuration", LINES)[0].thread
    greedy = bench.chunk("sampling", "greedy", bench.endpoint(QWEN))
    moved = archive.variation(theirs, {"sampling": greedy})
    head = bench.catalog.head(theirs).id
    return archive.edit(theirs, moved, head).variation.configuration.id


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
        {"detail": f"configuration {mine['id']} has nothing to follow"},
    )

    origin = _moved(bench)
    proposed = signed.get(proposal).json()
    assert proposed["origin_head"]["id"] == origin
    forked_from = signed.get(f"/api/threads/{mine['id']}").json()["forked_from"]
    assert proposed["base"]["id"] == forked_from
    assert proposed["varies"] == [] and proposed["component"] is None
    assert proposed["recipe"]["sampling"] == bench.chunk(
        "sampling", "greedy", bench.endpoint(QWEN)
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
