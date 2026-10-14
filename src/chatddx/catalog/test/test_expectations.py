import pytest
from pydantic import JsonValue

from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.catalog.test.memory import ALICE, ARCHIVE, BOB, Memory, owned
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case, Vignette
from chatddx.factors.scoring import Expectation, ExpectationSchema
from chatddx.factors.test.sample import fp, world


class Sample:
    def __init__(self) -> None:
        self.reg: Registry = Registry()
        self.case: str = world(self.reg)["case"]
        self.schema: str = self.reg.add(
            ExpectationSchema(json_schema={"type": "object"})
        )
        self.other_schema: str = self.reg.add(
            ExpectationSchema(json_schema={"type": "array"})
        )
        self.rows: Memory = Memory(self.reg)

    def expecting(
        self, *ddx: str, of: str | None = None, under: str | None = None
    ) -> str:
        data: JsonValue = {"ddx": list(ddx)}
        return self.reg.add(
            Expectation(
                case=of or self.case,
                expectation_schema=under or self.schema,
                data=data,
            )
        )


def test_expecting_gives_each_head_of_the_case_under_the_schema_and_what_is_said() -> (
    None
):
    s = Sample()
    rows = s.rows
    archive = owned(rows, rows.start(s.expecting("ACS")), ARCHIVE, ALICE)
    fork = owned(rows, rows.start(archive.digest, forked_from=archive.id), ALICE)
    bobs = owned(rows, rows.start(s.expecting("PE")), BOB, ALICE)
    _ = owned(rows, rows.start(s.expecting("PE", under=s.other_schema)), ALICE)
    mine = rows.save(fork.thread, s.expecting("ACS", "dissection"))
    rows.note(Subject(thread=bobs.thread), Entry(field=EntryField.DELETED))

    found = threads.expecting(rows, [s.case], s.schema)[s.case]
    assert [(e, a.owner, a.collaborators, a.deleted) for e, a in found] == [
        (archive, ARCHIVE, {ALICE}, False),
        (mine, ALICE, set(), False),
        (bobs, BOB, {ALICE}, True),
    ]


def test_expecting_gives_every_case_asked_for() -> None:
    s = Sample()
    rows = s.rows
    cough, rash = (
        s.reg.add(Case(vignette=Vignette(source="registry", id=id, fingerprint=fp(id))))
        for id in ("c2", "c3")
    )
    mine = owned(rows, rows.start(s.expecting("ACS")), ALICE)
    asthma = owned(rows, rows.start(s.expecting("asthma", of=cough)), ARCHIVE, ALICE)
    found = threads.expecting(rows, [s.case, cough, rash], s.schema)
    assert {c: [e for e, _ in held] for c, held in found.items()} == {
        s.case: [mine],
        cough: [asthma],
        rash: [],
    }


def test_one_head_is_picked_from_a_case_s_threads() -> None:
    assert threads.picked("c", {}) is None
    assert threads.picked("c", {1: "a", 2: "a"}) == "a"
    with pytest.raises(LookupError, match="case c has expectations to choose from, in"):
        _ = threads.picked("c", {2: "b", 1: "a"})


def test_a_person_owns_one_live_expectation_thread_per_case_and_schema() -> None:
    s = Sample()
    rows = s.rows
    check = threads.check_expectation
    to_alice = Entry(field=EntryField.OWNER, person=ALICE)
    deleted = Entry(field=EntryField.DELETED)
    restored = Entry(field=EntryField.DELETED, present=False)
    mine = owned(rows, rows.start(s.expecting("ACS")), ALICE)
    other = s.expecting("PE")

    second = rows.start(other)
    check(rows, second.thread)
    with pytest.raises(ValueError, match=f"already, in thread {mine.thread}"):
        check(rows, second.thread, entry=to_alice)
    check(rows, second.thread, entry=Entry(field=EntryField.OWNER, person=BOB))
    check(rows, second.thread, entry=Entry(field=EntryField.COLLABORATOR, person=ALICE))

    elsewhere = owned(rows, rows.start(s.expecting("PE", under=s.other_schema)), ALICE)
    with pytest.raises(ValueError, match="owns an expectation of case"):
        check(rows, elsewhere.thread, other)
    check(rows, mine.thread, other)

    rows.note(Subject(thread=mine.thread), deleted)
    check(rows, second.thread, entry=to_alice)
    _ = owned(rows, second, ALICE)
    with pytest.raises(ValueError, match=f"already, in thread {second.thread}"):
        check(rows, mine.thread, entry=restored)
    check(rows, second.thread, entry=deleted)
