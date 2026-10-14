import pytest

from chatddx.curation import init
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.identity import Person
from chatddx.scorers import metrics
from chatddx.scorers.scorer import Metrics
from chatddx.scorers.shipped import SCORERS
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection
from chatddx.test.world import world_plan

pytestmark = pytest.mark.solidified

SHIPPED = "chatddx.scorers.metrics:score"


def _scorers(lines: list[str]) -> set[str]:
    return {
        line.split(": ")[1].split(" ")[0]
        for line in lines
        if line.startswith("[archive scorer]")
    }


@pytest.mark.slow
@pytest.mark.parametrize("template", ["loaded"], indirect=True)
def test_a_deploy_moves_the_archive_s_scorers_on_when_it_raises_their_version(
    conn: Connection, alice: Person, monkeypatch: pytest.MonkeyPatch
) -> None:
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
