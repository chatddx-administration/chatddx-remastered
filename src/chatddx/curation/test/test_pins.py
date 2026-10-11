import pytest

from chatddx.conftest import sample_plan
from chatddx.curation import init
from chatddx.curation.test.sample import SOME, vignettes
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.scorers import patterns
from chatddx.scorers.scorer import Metrics
from chatddx.scorers.shipped import SCORERS
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection

pytestmark = pytest.mark.wip

PATTERNS = "chatddx.scorers.patterns:score"


def _scorers(lines: list[str]) -> set[str]:
    return {
        line.split(": ")[1].split(" ")[0]
        for line in lines
        if line.startswith("[archive scorer]")
    }


# The archive's scorers pin the version of their entry point the running code ships, so
# a deploy moves them on only when it raises that version.
@pytest.mark.slow
def test_a_deploy_moves_the_archive_s_scorers_on_when_it_raises_their_version(
    conn: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    alice = People(conn).add("alice", "Alice")
    monkeypatch.setenv("CHATDDX_REVISION", "e" * 40)
    _ = init(conn, sample_plan(), SOME, vignettes(), alice)

    monkeypatch.setenv("CHATDDX_REVISION", "f" * 40)
    assert _scorers(init(conn, sample_plan(), SOME, vignettes(), alice)) == {
        "validated"
    }

    monkeypatch.setitem(SCORERS, PATTERNS, Metrics(2, patterns.score.metrics))
    assert _scorers(init(conn, sample_plan(), SOME, vignettes(), alice)) == {"updated"}
    catalog, store = Catalog(conn), Store(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [thread] = catalog.find("scorer", "diagnoses", owner=archive.id)
    head = catalog.head(thread)
    assert resolve(store.get, head.digest, Scorer).version == 2
    assert catalog.labels(head.id) == {
        ("view", 0): "differential",
        ("view", 1): "dont-miss",
    }
