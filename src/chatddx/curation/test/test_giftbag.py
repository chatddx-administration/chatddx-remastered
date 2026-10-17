import pytest

from chatddx.catalog import Entry, EntryField, Subject, read, threads
from chatddx.curation import init
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.factors.base import Fingerprint
from chatddx.factors.cases import Case, Vignette
from chatddx.factors.scoring import Expectation
from chatddx.identity import Person, owns
from chatddx.store import Catalog, People, Rows, Store
from chatddx.store.store import Connection
from chatddx.test.world import world_plan


def _case(id: str) -> str:
    raw = vignettes().fetch(id)
    vignette = Vignette(source="test", id=id, fingerprint=Fingerprint.of(raw))
    return Case(vignette=vignette).digest


def _own(conn: Connection, alice: Person, case: str) -> tuple[str, str]:
    store, catalog = Store(conn), Catalog(conn)
    rows = Rows(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [thread] = [
        t
        for t in threads.expectations_of(rows, case)
        if read.about(rows, Subject(thread=t)).owner == archive.id
    ]
    held = store.get(threads.head(rows, thread).digest)
    assert isinstance(held, Expectation)
    registry = store.load([held.digest])
    mine = registry.add(
        Expectation(case=case, expectation_schema=held.expectation_schema, data="mine")
    )
    _ = store.add(registry, [mine])
    _ = catalog.create(mine, alice.id)
    return mine, held.expectation_schema


@pytest.mark.parametrize("template", ["loaded"], indirect=True)
@pytest.mark.slow
def test_the_giftbag_keeps_a_person_s_own_expectation(
    conn: Connection, alice: Person
) -> None:
    catalog = Catalog(conn)
    rows = Rows(conn)
    plan = world_plan()
    noted, crlf = _case("noted"), _case("crlf")
    written, schema = _own(conn, alice, noted)

    lines = init(conn, plan, CASES, vignettes(), alice, giftbag=True)
    assert "[giftbag expectation] noted: kept their own" in lines
    assert any(l.startswith("[giftbag expectation] crlf: forked") for l in lines)

    [fork] = [
        e.thread
        for e, a in threads.expecting(rows, [crlf], schema)[crlf]
        if owns(alice.id, a)
    ]
    catalog.note(Subject(thread=fork), Entry(field=EntryField.DELETED), alice.id)
    again, _ = _own(conn, alice, crlf)
    lines = init(conn, plan, CASES, vignettes(), alice, giftbag=True)
    assert "[giftbag expectation] crlf: kept their own" in lines
    assert read.about(rows, Subject(thread=fork)).deleted
    assert {
        case: [e.digest for e, a in held if owns(alice.id, a)]
        for case, held in threads.expecting(rows, [noted, crlf], schema).items()
    } == {noted: [written], crlf: [again]}
