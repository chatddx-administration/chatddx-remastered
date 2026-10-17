from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import psycopg
from pydantic import JsonValue

from chatddx import settings
from chatddx.bench import Bench
from chatddx.catalog import Edit, Entry, EntryField, Subject
from chatddx.curation import Plan
from chatddx.factors.base import Finding, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import LocalModel
from chatddx.factors.facts import ModelFacts
from chatddx.factors.scoring import Expectation
from chatddx.factors.trial import Trial
from chatddx.identity import Person
from chatddx.inventory import DirectorySource, World
from chatddx.ledger import Endpoint, Run, RunStarted
from chatddx.rig import rig
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection
from chatddx.test.world import QWEN, TEST

SOURCE = World.load(TEST).inventory.source(kind=DirectorySource)
UNSERVED = "http://127.0.0.1:9/v1/"


def trial(conn: Connection, plan: Plan, recipe: str, *ids: str) -> Trial:
    cases = [c for c in SOURCE.cases() if c.vignette.id in ids]
    made = Trial(
        skeleton=plan.named("recipe", recipe).digest,
        engine=plan.named("local_engine", QWEN).digest,
        cases=tuple(plan.registry.add(c) for c in cases),
        seeds=(7,),
    )
    _ = Store(conn).add(plan.registry, [plan.registry.add(made)])
    return made


def ran(
    conn: Connection,
    by: Person,
    made: Trial,
    finished: bool = True,
    endpoint: str | None = None,
    findings: Sequence[Finding] = (),
) -> UUID:
    started = RunStarted(
        run=uuid4(),
        at=datetime.now(UTC),
        rig=rig(),
        trial=made.digest,
        endpoint=None if endpoint is None else Endpoint(name=endpoint, url=UNSERVED),
    )
    store = Store(conn)
    store.append(started)
    Catalog(conn).note(
        Subject(run=started.run), Entry(field=EntryField.OWNER, person=by.id), by.id
    )
    if finished:
        store.append(Run(stages=(started,)).finish(datetime.now(UTC), findings))
    return started.run


def another_expectation(bench: Bench, case: str, data: JsonValue) -> str:
    [schema] = bench.expectation_schemas(case)
    held = bench.expectation(case, schema)
    assert held is not None
    store, catalog, person = Store(bench.conn), Catalog(bench.conn), bench.person.id
    [mine] = bench.expectation_choices([case], schema)[case]
    registry = store.load([held.digest])
    other = registry.add(
        Expectation(case=held.case, expectation_schema=schema, data=data)
    )
    _ = store.add(registry, [other])
    catalog.note(Subject(thread=mine), Entry(field=EntryField.DELETED), person)
    restored = Entry(field=EntryField.DELETED, present=False)
    dbname = bench.conn.info.dbname
    with (
        psycopg.connect(settings.database(), dbname=dbname, autocommit=True) as rival,
        bench.conn.transaction(),
    ):
        catalog.note(Subject(thread=mine), restored, person)
        _ = Catalog(rival).create(other, person)
    return other


# As init-data writes a corrected facts file: a new version of the archive's thread.
def move_model(bench: Bench, name: str, **changes: JsonValue) -> Edit:
    [thread] = bench.catalog.find("model.local", name)
    held = resolve(bench.get, bench.catalog.head(thread).digest, LocalModel)
    newer = LocalModel.model_validate({**held.model_dump(mode="json"), **changes})
    registry = Registry()
    _ = Store(bench.conn).add(registry, [registry.add(newer)])
    archive = People(bench.conn).find("archive")
    assert archive is not None
    return bench.catalog.edit(thread, newer.digest, archive.id)


def correct_facts(bench: Bench, model: str, **changes: JsonValue) -> Edit:
    held = bench.facts.models[model].model_dump(mode="json")
    newer = ModelFacts.model_validate({**held, **changes})
    registry = Registry()
    _ = Store(bench.conn).add(registry, [registry.add(newer)])
    archive = People(bench.conn).find("archive")
    assert archive is not None
    [thread] = bench.catalog.find("facts", model)
    return bench.catalog.edit(thread, newer.digest, archive.id)
