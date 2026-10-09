from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import JsonValue

from chatddx.bench import Bench
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.conftest import WORLDS
from chatddx.core.rig import rig
from chatddx.curation import Plan
from chatddx.factors.scoring import Expectation
from chatddx.factors.trial import Trial
from chatddx.identity import Person
from chatddx.inventory import DirectorySource
from chatddx.ledger import Run, RunStarted
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection

SOURCE = DirectorySource(name="sample", path=WORLDS / "sample" / "vignettes")
FREE_TEXT = "free-text (Qwen/Qwen3-8B-AWQ)"
PLAN = "plan (Qwen/Qwen3-8B-AWQ)"
QWEN = "qwen3-8b-awq@fake"


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


# A second expectation thread of the person's own for a case, in the schema of the one
# they read, so that there are two to choose from.
def another_expectation(bench: Bench, case: str, data: JsonValue) -> str:
    [schema] = bench.expectation_schemas(case)
    held = bench.expectation(case, schema)
    assert held is not None
    store = Store(bench.conn)
    registry = store.load([held.digest])
    other = registry.add(
        Expectation(case=held.case, expectation_schema=schema, data=data)
    )
    _ = store.add(registry, [other])
    _ = Catalog(bench.conn).create(other, bench.person.id)
    return other
