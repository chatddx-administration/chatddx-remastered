import re

import pytest

from chatddx.bench import Ambiguous, Bench, NotFound, made_for
from chatddx.bench.test.sample import (
    FREE_TEXT,
    PLAN,
    QWEN,
    another_expectation,
    ran,
    trial,
)
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.curation import Plan, load_cases
from chatddx.curation.plan import SAMPLE
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation
from chatddx.identity import Person
from chatddx.runner.score import score_run
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection


def test_a_person_sees_their_own_and_shared_threads_and_families(
    conn: Connection, alice: Person, bob: Person, bench: Bench
) -> None:
    owners = {a.owner for _, a in bench.threads("configuration")}
    archive = People(conn).find("archive")
    assert archive is not None and owners == {alice.id, archive.id}

    mine, _ = bench.thread("configuration", FREE_TEXT)
    assert bench.about(mine.thread).owner == alice.id
    theirs, _ = bench.thread("configuration", f"archive/{FREE_TEXT}")
    assert bench.about(theirs.thread).owner == archive.id
    assert theirs.digest == mine.digest and theirs.thread != mine.thread
    with pytest.raises(NotFound, match="no configuration 'nothing' for alice"):
        _ = bench.thread("configuration", "nothing")

    families = bench.families()
    assert len(families) == len(load_cases(SAMPLE))
    assert {f.about.language for f in families} == {"en", "sv"}
    assert all(f.about.tags for f in families)
    bobs = Bench(conn, bob, bench.inventory, bench.facts)
    assert bobs.threads("configuration") == [] and bobs.families() == []


def test_a_case_is_found_by_its_name_or_as_owner_slash_name(bench: Bench) -> None:
    found = bench.family("Dutchfall11w")
    assert bench.family("archive/Dutchfall11w") == found
    with pytest.raises(NotFound, match="no case 'alice/Dutchfall11w' for alice"):
        _ = bench.family("alice/Dutchfall11w")
    with pytest.raises(NotFound, match="no case 'nope' for alice"):
        _ = bench.family("nope")


def test_a_person_finds_their_runs_and_those_that_reach_a_digest(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    free_text = trial(conn, plan, FREE_TEXT, "DutchFall10w", "casesfromedn1")
    planned = trial(conn, plan, PLAN, "DutchFall10w")
    first = ran(conn, alice, free_text)
    second = ran(conn, alice, planned)
    _ = ran(conn, bob, free_text)
    gone = ran(conn, alice, planned)
    Catalog(conn).note(Subject(run=gone), Entry(field=EntryField.DELETED), alice.id)

    assert [r.run for r in bench.runs()] == [second, first]
    assert bench.run().run == second
    assert bench.run(str(first)[:8]).run == first
    with pytest.raises(Ambiguous, match="2 runs of yours start with ''"):
        _ = bench.run("")
    with pytest.raises(NotFound, match="no run of yours"):
        _ = bench.run("zzz")

    assert [r.run for r in bench.reaching(free_text.skeleton)] == [first]
    [shared_case] = set(free_text.cases) & set(planned.cases)
    assert [r.run for r in bench.reaching(shared_case)] == [second, first]
    store = Store(conn)
    assert len(store.runs_of(free_text.digest)) == 2
    assert store.finished([first, second, gone]) == {first, second, gone}


def test_a_run_is_left_to_score_until_scored_under_the_scoring_built_now(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    made = trial(conn, plan, FREE_TEXT, "DutchFall10w", "casesfromedn1")
    run = ran(conn, alice, made)
    _ = ran(conn, alice, made, finished=False)
    started = bench.run(str(run))
    assert {a.name for _, a in bench.scorers_for(started)} == {"free-text", "raw"}

    scorer = plan.named("scorer", "free-text").digest
    raw = plan.named("scorer", "raw").digest
    assert set(bench.unscored(started)) == {scorer, raw}
    assert [(r.run, set(s)) for r, s in bench.outstanding()] == [(run, {scorer, raw})]
    scoring = bench.scoring(started, scorer)
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
    rebuilt = bench.scoring(started, scorer)
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


def test_a_per_model_configuration_is_picked_by_the_engine_s_model(
    bench: Bench,
) -> None:
    with pytest.raises(NotFound) as refused:
        _ = bench.configuration("plan")
    assert refused.value.per_model == (PLAN, "plan (en, openai/gpt-oss-20b)")

    variation = bench.configuration("plan", bench.endpoint(QWEN))
    assert (variation.name, variation.label, variation.parts) == (PLAN, PLAN, {})

    with pytest.raises(NotFound) as refused:
        _ = bench.configuration("nope", bench.endpoint(QWEN))
    assert refused.value.per_model == ()


def test_a_configuration_made_in_several_languages_is_named_whole(
    bench: Bench, alice: Person
) -> None:
    engine = bench.endpoint(QWEN)
    english = bench.configuration("plan", engine).configuration
    swedish = "plan (sv, Qwen/Qwen3-8B-AWQ)"
    _ = bench.catalog.create(english.digest, alice.id, name=swedish)
    several = f"made in more than one language: {PLAN}, {swedish}"
    with pytest.raises(Ambiguous, match=re.escape(several)):
        _ = bench.configuration("plan", engine)
    assert bench.configuration(swedish, engine).name == swedish
    models = ["Qwen/Qwen3-8B-AWQ"]
    assert [made_for(n, models) for n in (swedish, "web (en)", "off (sv)")] == [
        ("plan", "sv", "Qwen/Qwen3-8B-AWQ"),
        ("web", "en", None),
        ("off", "sv", None),
    ]
    assert made_for("plan (Qwen/Qwen3-8B-AWQ)", models) == ("plan", None, models[0])
    assert made_for("a (b) c", models) is None
    assert made_for("plan (sv, other/model)", models) is None


def test_a_variation_compiles_to_a_skeleton_of_its_own(bench: Bench) -> None:
    engine = bench.endpoint(QWEN)
    configuration = bench.configuration(FREE_TEXT, engine)
    off = configuration.set("reasoning", bench.chunk("reasoning", "off", engine), "off")

    assert bench.skeleton(configuration).digest == configuration.configuration.digest
    assert bench.skeleton(off).digest != configuration.configuration.digest
    assert bench.skeleton(off).body["chat_template_kwargs"] == {
        "enable_thinking": False
    }


def test_several_configurations_of_one_name_are_refused_a_save(bench: Bench) -> None:
    variation = bench.configuration(FREE_TEXT, bench.endpoint(QWEN))
    _ = Catalog(bench.conn).create(
        variation.configuration.digest, bench.person.id, name="twice"
    )
    _ = Catalog(bench.conn).create(
        variation.configuration.digest, bench.person.id, name="twice"
    )

    with pytest.raises(Ambiguous, match="2 configurations named 'twice'"):
        _ = bench.save(variation, "twice")
