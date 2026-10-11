import pytest

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.conftest import sample_plan
from chatddx.curation import init
from chatddx.curation.test.sample import SOME, vignettes
from chatddx.factors.base import Fingerprint
from chatddx.factors.cases import Case, Vignette
from chatddx.factors.scoring import Expectation
from chatddx.identity import Person
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection

pytestmark = pytest.mark.wip


def _case(id: str) -> str:
    raw = vignettes().fetch(id)
    vignette = Vignette(source="sample", id=id, fingerprint=Fingerprint.of(raw))
    return Case(vignette=vignette).digest


def _own(conn: Connection, alice: Person, case: str) -> tuple[str, str]:
    store, catalog = Store(conn), Catalog(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [thread] = [
        t
        for t in catalog.expectations_of(case)
        if catalog.about(Subject(thread=t)).owner == archive.id
    ]
    held = store.get(catalog.head(thread).digest)
    assert isinstance(held, Expectation)
    registry = store.load([held.digest])
    mine = registry.add(
        Expectation(case=case, expectation_schema=held.expectation_schema, data="mine")
    )
    _ = store.add(registry, [mine])
    _ = catalog.create(mine, alice.id)
    return mine, held.expectation_schema


@pytest.mark.slow
def test_the_giftbag_keeps_a_person_s_own_expectation(conn: Connection) -> None:
    alice = People(conn).add("alice", "Alice")
    catalog = Catalog(conn)
    plan = sample_plan()
    _ = init(conn, plan, SOME, vignettes(), alice)
    eleven, fall = _case("Dutchfall11w"), _case("DutchFall10w")
    written, schema = _own(conn, alice, eleven)

    lines = init(conn, plan, SOME, vignettes(), alice, giftbag=True)
    assert "[giftbag expectation] Dutchfall11w: kept their own" in lines
    assert any(
        l.startswith("[giftbag expectation] DutchFall10w: forked") for l in lines
    )

    [fork] = catalog.expectation_choices([fall], alice.id, schema)[fall]
    catalog.note(Subject(thread=fork), Entry(field=EntryField.DELETED), alice.id)
    again, _ = _own(conn, alice, fall)
    lines = init(conn, plan, SOME, vignettes(), alice, giftbag=True)
    assert "[giftbag expectation] DutchFall10w: kept their own" in lines
    assert catalog.about(Subject(thread=fork)).deleted
    assert catalog.expectations_for([eleven, fall], alice.id, schema) == {
        eleven: written,
        fall: again,
    }
