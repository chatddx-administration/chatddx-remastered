from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import psycopg
import pytest

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.conftest import (
    WORLDS,
    connect,
    create_database,
    drop_database,
    sample_plan,
)
from chatddx.core import settings
from chatddx.core.rig import rig
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation, Scorer
from chatddx.factors.trial import Trial
from chatddx.identity import Person
from chatddx.inventory import DirectorySource
from chatddx.ledger import Run, RunStarted
from chatddx.runner.score import score_run
from chatddx.seed import Plan, load_cases, seed
from chatddx.seed.plan import SAMPLE
from chatddx.store import Catalog, People, Reads, Store
from chatddx.store.store import Connection

SOURCE = DirectorySource(name="sample", path=WORLDS / "sample" / "vignettes")
FREE_TEXT = "free-text (Qwen/Qwen3-8B-AWQ)"
PLAN = "plan (Qwen/Qwen3-8B-AWQ)"


@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


# The sample as init-data lands it: the archive's threads and families, shared with
# alice, and her giftbag of forks. Seeded once, and copied for each test.
@pytest.fixture(scope="module")
def seeded(migrated: str) -> Iterator[str]:
    name = create_database(template=migrated)
    try:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            cases = load_cases(SAMPLE / "cases.toml")
            _ = seed(conn, sample_plan(), cases, SOURCE, alice, giftbag=True)
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def db(seeded: str) -> Iterator[str]:
    name = create_database(template=seeded)
    try:
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def conn(db: str) -> Iterator[Connection]:
    with psycopg.connect(settings.database(), dbname=db, autocommit=True) as c:
        yield c


@pytest.fixture
def alice(conn: Connection) -> Person:
    found = People(conn).find("alice")
    assert found is not None
    return found


@pytest.fixture
def bob(conn: Connection) -> Person:
    return People(conn).add("bob", "Bob")


def trial(conn: Connection, plan: Plan, recipe: str, *ids: str) -> Trial:
    cases = [c for c in SOURCE.cases() if c.vignette.id in ids]
    made = Trial(
        skeleton=plan.named("recipe", recipe).digest,
        engine=plan.named("local_engine", "qwen3-8b-awq@fake").digest,
        cases=tuple(plan.registry.add(c) for c in cases),
        seeds=(7,),
    )
    _ = Store(conn).add(plan.registry, [plan.registry.add(made)])
    return made


# A run's log without items, which is all the reads look at.
def ran(conn: Connection, by: Person, made: Trial, finished: bool = True) -> UUID:
    started = RunStarted(
        run=uuid4(), at=datetime.now(UTC), rig=rig(), trial=made.digest
    )
    store = Store(conn)
    store.append(started)
    Catalog(conn).note(
        Subject(run=started.run), Entry(field=EntryField.OWNER, person=by.id), by.id
    )
    if finished:
        store.append(Run(stages=(started,)).finish(datetime.now(UTC)))
    return started.run


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


def test_a_run_is_outstanding_until_scored_under_the_scoring_built_now(
    conn: Connection, alice: Person, plan: Plan
) -> None:
    made = trial(conn, plan, FREE_TEXT, "DutchFall10w", "casesfromedn1")
    run = ran(conn, alice, made)
    _ = ran(conn, alice, made, finished=False)
    reads = Reads(conn, alice)
    started = reads.run(str(run))
    assert {a.name for _, a in reads.scorers(started)} == {"free-text", "raw"}

    scorer = plan.named("scorer", "free-text").digest
    assert [r.run for r in reads.outstanding(scorer)] == [run]
    scoring = reads.scoring(started, scorer)
    assert scoring is not None and len(scoring.expectations) == 2
    store = Store(conn)
    registry = store.load([scorer, *scoring.expectations])
    _, findings = score_run(conn, run, scoring, registry, alice)
    assert findings == []
    assert reads.outstanding(scorer) == []
    assert [s.scoring for s in store.scores_of(run)] == [scoring.digest]

    catalog = Catalog(conn)
    case = made.cases[0]
    [thread] = [
        t
        for t in catalog.expectations_of(case)
        if catalog.about(Subject(thread=t)).owner == alice.id
    ]
    head = resolve(store.get, catalog.head(thread).digest, Expectation)
    edited = head.model_copy(update={"data": {"diagnosis": {"pattern": "sepsis"}}})
    _ = store.add(plan.registry, [plan.registry.add(edited)])
    _ = catalog.edit(thread, edited.digest, alice.id)
    assert [r.run for r in reads.outstanding(scorer)] == [run]
    rebuilt = reads.scoring(started, scorer)
    assert rebuilt is not None and edited.digest in rebuilt.expectations
    assert (
        resolve(store.get, scorer, Scorer).expectation_schema == head.expectation_schema
    )
