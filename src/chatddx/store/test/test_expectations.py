import pytest

from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.scoring import Expectation, ExpectationSchema, Scoring
from chatddx.factors.test.sample import world
from chatddx.identity import owns
from chatddx.store import Catalog, People, Rows, Store
from chatddx.store.store import Connection


def test_the_catalog_refuses_a_person_a_second_expectation_of_a_case(
    conn: Connection,
) -> None:
    reg = Registry()
    ids = world(reg)
    [held] = resolve(reg.get, ids["scoring"], Scoring).expectations
    first = resolve(reg.get, held, Expectation)
    case, schema = first.case, first.expectation_schema
    other_schema = reg.add(ExpectationSchema(json_schema={"type": "array"}))
    other = reg.add(Expectation(case=case, expectation_schema=schema, data={"x": 1}))
    elsewhere = reg.add(
        Expectation(case=case, expectation_schema=other_schema, data=[1])
    )
    store, catalog, people = Store(conn), Catalog(conn), People(conn)
    rows = Rows(conn)
    _ = store.add(reg, [ids["scoring"], other, elsewhere])
    alice, bob = people.add("alice", "Alice"), people.add("bob", "Bob")

    mine = catalog.create(first.digest, alice.id)
    with pytest.raises(ValueError, match=f"already, in thread {mine.thread}"):
        _ = catalog.create(other, alice.id)
    theirs = catalog.create(other, bob.id)
    to_alice = Entry(field=EntryField.OWNER, person=alice.id)
    with pytest.raises(ValueError, match="owns an expectation of case"):
        catalog.note(Subject(thread=theirs.thread), to_alice, bob.id)
    apart = catalog.create(elsewhere, alice.id)
    with pytest.raises(ValueError, match="owns an expectation of case"):
        _ = catalog.edit(apart.thread, other, alice.id)

    catalog.note(Subject(thread=mine.thread), Entry(field=EntryField.DELETED), alice.id)
    catalog.note(Subject(thread=theirs.thread), to_alice, bob.id)
    restored = Entry(field=EntryField.DELETED, present=False)
    with pytest.raises(ValueError, match=f"already, in thread {theirs.thread}"):
        catalog.note(Subject(thread=mine.thread), restored, alice.id)

    expecting = threads.expecting(rows, [case], schema)[case]
    assert [e.digest for e, a in expecting if owns(alice.id, a)] == [other]
    assert [e.digest for e in threads.history(rows, apart.thread)] == [elsewhere]
    heads = threads.heads(rows, "expectation")
    assert [e.thread for e, a in heads if not a.deleted] == [
        theirs.thread,
        apart.thread,
    ]
    assert [e.thread for e, a in heads if a.deleted] == [mine.thread]
