import pytest

from chatddx.bench import Bench
from chatddx.bench.test.sample import FREE_TEXT, another_expectation, ran, trial
from chatddx.catalog import Subject
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation
from chatddx.identity import Person
from chatddx.runner.score import score_run
from chatddx.seed import Plan
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection


def test_a_run_is_left_to_score_until_scored_under_the_scoring_built_now(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    made = trial(conn, plan, FREE_TEXT, "DutchFall10w", "casesfromedn1")
    run = ran(conn, alice, made)
    _ = ran(conn, alice, made, finished=False)
    started = bench.run(str(run))
    assert {a.name for _, a in bench.reads.scorers(started)} == {"free-text", "raw"}

    scorer = plan.named("scorer", "free-text").digest
    raw = plan.named("scorer", "raw").digest
    assert set(bench.unscored(started)) == {scorer, raw}
    assert [(r.run, set(s)) for r, s in bench.outstanding()] == [(run, {scorer, raw})]
    scoring = bench.reads.scoring(started, scorer)
    assert scoring is not None and len(scoring.expectations) == 2
    store = Store(conn)
    registry = store.load([scorer, *scoring.expectations])
    _, findings = score_run(conn, run, scoring, registry, alice)
    assert findings == []
    assert bench.unscored(started) == [raw]
    assert [s.scoring for s in store.scores_of(run)] == [scoring.digest]

    catalog = Catalog(conn)
    [thread] = [
        t
        for t in catalog.expectations_of(made.cases[0])
        if catalog.about(Subject(thread=t)).owner == alice.id
    ]
    head = resolve(store.get, catalog.head(thread).digest, Expectation)
    registry = store.load([head.digest])
    edited = registry.add(
        Expectation(
            case=head.case,
            expectation_schema=head.expectation_schema,
            data={"diagnosis": {"pattern": "sepsis"}},
        )
    )
    _ = store.add(registry, [edited])
    _ = catalog.edit(thread, edited, alice.id)
    assert set(bench.unscored(started)) == {scorer, raw}
    rebuilt = bench.reads.scoring(started, scorer)
    assert rebuilt is not None and edited in rebuilt.expectations


def test_a_case_is_held_to_the_expectation_scoring_picks(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    case = bench.family("Dutchfall11w").case
    schema = plan.named("expectation_schema", "targets").digest
    assert bench.expectation_schemas(case) == [schema]

    held = bench.expectation(case, schema)
    assert held is not None
    assert held.digest == Catalog(conn).expectation_for(case, alice.id, schema)

    theirs = Bench(conn, bob, bench.inventory, bench.facts)
    assert theirs.expectation_schemas(case) == []
    assert theirs.expectation(case, schema) is None


def test_several_expectations_to_choose_from_are_refused(bench: Bench) -> None:
    case = bench.family("Dutchfall11w").case
    _ = another_expectation(bench, case, {"diagnosis": {"pattern": "sepsis"}})
    [schema] = bench.expectation_schemas(case)

    with pytest.raises(LookupError, match="has expectations to choose from"):
        _ = bench.expectation(case, schema)
