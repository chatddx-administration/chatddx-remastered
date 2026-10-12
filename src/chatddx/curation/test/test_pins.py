import pytest

from chatddx.curation import init
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.scorers import metrics
from chatddx.scorers.scorer import Metrics
from chatddx.scorers.shipped import SCORERS
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection
from chatddx.test.world import world_plan

pytestmark = pytest.mark.wip

SHIPPED = "chatddx.scorers.metrics:score"


def _scorers(lines: list[str]) -> set[str]:
    return {
        line.split(": ")[1].split(" ")[0]
        for line in lines
        if line.startswith("[archive scorer]")
    }


@pytest.mark.slow
def test_a_deploy_moves_the_archive_s_scorers_on_when_it_raises_their_version(
    conn: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    alice = People(conn).add("alice", "Alice")
    monkeypatch.setenv("CHATDDX_REVISION", "e" * 40)
    _ = init(conn, world_plan(), CASES, vignettes(), alice)

    monkeypatch.setenv("CHATDDX_REVISION", "f" * 40)
    assert _scorers(init(conn, world_plan(), CASES, vignettes(), alice)) == {
        "validated"
    }

    raised = metrics.score.version + 1
    monkeypatch.setitem(SCORERS, SHIPPED, Metrics(raised, metrics.score.metrics))
    assert _scorers(init(conn, world_plan(), CASES, vignettes(), alice)) == {"updated"}
    catalog, store = Catalog(conn), Store(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [thread] = catalog.find("scorer", "list", owner=archive.id)
    head = catalog.head(thread)
    assert resolve(store.get, head.digest, Scorer).version == raised
    assert catalog.labels(head.id) == {
        ("view", 0): "differential",
        ("view", 1): "dont-miss",
    }
