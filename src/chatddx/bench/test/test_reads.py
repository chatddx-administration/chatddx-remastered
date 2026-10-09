import pytest

from chatddx.bench import Reads
from chatddx.bench.test.sample import FREE_TEXT, PLAN, ran, trial
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.identity import Person
from chatddx.seed import Plan, load_cases
from chatddx.seed.plan import SAMPLE
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection


def test_a_person_sees_their_own_and_shared_threads_and_families(
    conn: Connection, alice: Person, bob: Person
) -> None:
    reads = Reads(conn, alice)
    seen = reads.threads("skeleton")
    owners = {a.owner for _, a in seen}
    archive = People(conn).find("archive")
    assert archive is not None and owners == {alice.id, archive.id}

    mine = reads.thread("skeleton", FREE_TEXT)
    assert Catalog(conn).about(Subject(thread=mine.thread)).owner == alice.id
    theirs = reads.thread("skeleton", f"archive/{FREE_TEXT}")
    assert Catalog(conn).about(Subject(thread=theirs.thread)).owner == archive.id
    assert theirs.digest == mine.digest and theirs.thread != mine.thread
    with pytest.raises(LookupError, match="no skeleton named 'nothing'"):
        _ = reads.thread("skeleton", "nothing")

    families = reads.families()
    assert len(families) == len(load_cases(SAMPLE / "cases.toml"))
    languages = {a.language for _, a in families}
    assert languages == {"en", "sv"}
    assert all(a.tags for _, a in families)
    assert Reads(conn, bob).threads("skeleton") == []
    assert Reads(conn, bob).families() == []


def test_a_person_finds_their_runs_and_those_that_reach_a_digest(
    conn: Connection, alice: Person, bob: Person, plan: Plan
) -> None:
    free_text = trial(conn, plan, FREE_TEXT, "DutchFall10w", "casesfromedn1")
    planned = trial(conn, plan, PLAN, "DutchFall10w")
    first = ran(conn, alice, free_text)
    second = ran(conn, alice, planned)
    _ = ran(conn, bob, free_text)
    gone = ran(conn, alice, planned)
    Catalog(conn).note(Subject(run=gone), Entry(field=EntryField.DELETED), alice.id)

    reads = Reads(conn, alice)
    assert [r.run for r in reads.runs()] == [second, first]
    assert reads.run(str(first)[:8]).run == first
    with pytest.raises(LookupError, match="2 runs of yours start with ''"):
        _ = reads.run("")
    with pytest.raises(LookupError, match="no run of yours"):
        _ = reads.run("zzz")

    assert [r.run for r in reads.reaching(free_text.skeleton)] == [first]
    [shared_case] = set(free_text.cases) & set(planned.cases)
    assert [r.run for r in reads.reaching(shared_case)] == [second, first]
    store = Store(conn)
    assert len(store.runs_of(free_text.digest)) == 2
    assert store.finished([first, second, gone]) == {first, second, gone}
