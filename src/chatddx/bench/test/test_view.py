import re

import pytest

from chatddx.bench import Ambiguous, Bench, NotFound
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

pytestmark = pytest.mark.wip


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


@pytest.mark.slow
def test_a_case_is_found_by_its_name_or_as_owner_slash_name(bench: Bench) -> None:
    found = bench.family("Dutchfall11w")
    assert bench.family("archive/Dutchfall11w") == found
    with pytest.raises(NotFound, match="no case 'alice/Dutchfall11w' for alice"):
        _ = bench.family("alice/Dutchfall11w")
    with pytest.raises(NotFound, match="no case 'nope' for alice"):
        _ = bench.family("nope")


def test_threads_cases_and_runs_are_found_by_id_among_what_the_person_sees(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    mine, _ = bench.thread("configuration", FREE_TEXT)
    assert bench.thread_by_id(mine.thread) == (mine, bench.about(mine.thread))
    assert bench.thread_by_id(mine.thread, "configuration")[0] == mine
    with pytest.raises(NotFound, match=f"no reasoning {mine.thread} for alice"):
        _ = bench.thread_by_id(mine.thread, "reasoning")
    with pytest.raises(NotFound, match="no thread 0 for alice"):
        _ = bench.thread_by_id(0)
    bobs = Bench(conn, bob, bench.inventory, bench.facts)
    with pytest.raises(NotFound, match=f"no thread {mine.thread} for bob"):
        _ = bobs.thread_by_id(mine.thread)
    Catalog(conn).note(
        Subject(thread=mine.thread), Entry(field=EntryField.DELETED), alice.id
    )
    with pytest.raises(NotFound):
        _ = bench.thread_by_id(mine.thread)

    family = bench.family("Dutchfall11w")
    assert bench.family_by_id(family.id) == family
    with pytest.raises(NotFound, match=f"no case {family.id} for bob"):
        _ = bobs.family_by_id(family.id)
    with pytest.raises(NotFound, match="no case 0 for alice"):
        _ = bench.family_by_id(0)

    made = trial(conn, plan, FREE_TEXT, "DutchFall10w")
    own, theirs = ran(conn, alice, made), ran(conn, bob, made)
    assert bench.run_by_id(own).run == own
    with pytest.raises(NotFound, match=f"no run {theirs} of yours"):
        _ = bench.run_by_id(theirs)


def test_a_variation_is_made_from_a_configuration_s_id_and_digests(
    bench: Bench,
) -> None:
    engine = bench.endpoint(QWEN)
    named = bench.configuration(FREE_TEXT, engine)
    off = bench.chunk("reasoning", "off", engine)
    thread = named.configuration.thread

    assert bench.variation(thread) == named
    varied = bench.variation(thread, {"reasoning": off})
    assert bench.skeleton(varied) == bench.skeleton(named.set("reasoning", off, "off"))
    with pytest.raises(ValueError, match="isn't a stored chunk of prompt"):
        _ = bench.variation(thread, {"prompt": off})
    with pytest.raises(ValueError, match="no part 'stack'"):
        _ = bench.variation(thread, {"stack": off})
    with pytest.raises(ValueError, match="can be taken out"):
        _ = bench.variation(thread, {"prompt": None})
    chunk = bench.thread("reasoning", "off", bench.model(engine))[0].thread
    with pytest.raises(NotFound, match=f"no configuration {chunk} for alice"):
        _ = bench.variation(chunk)


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


def test_several_expectations_to_choose_from_are_ambiguous(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    made = trial(conn, plan, FREE_TEXT, "DutchFall10w")
    [case] = made.cases
    _ = another_expectation(bench, case, {"diagnosis": {"pattern": "sepsis"}})
    [schema] = bench.expectation_schemas(case)
    scorer = plan.named("scorer", "free-text").digest
    started = bench.run_by_id(ran(conn, alice, made))

    with pytest.raises(Ambiguous, match="has expectations to choose from"):
        _ = bench.expectation(case, schema)
    with pytest.raises(Ambiguous, match="has expectations to choose from"):
        _ = bench.scoring(started, scorer)


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


def test_a_variation_compiles_to_a_skeleton_of_its_own(bench: Bench) -> None:
    engine = bench.endpoint(QWEN)
    configuration = bench.configuration(FREE_TEXT, engine)
    off = configuration.set("reasoning", bench.chunk("reasoning", "off", engine), "off")

    assert bench.skeleton(configuration).digest == configuration.configuration.digest
    assert bench.skeleton(off).digest != configuration.configuration.digest
    assert bench.skeleton(off).body["chat_template_kwargs"] == {
        "enable_thinking": False
    }


def test_a_variation_s_request_shows_placeholders_for_what_it_is_sent_with(
    bench: Bench,
) -> None:
    engine = bench.endpoint(QWEN)
    variation = bench.configuration(FREE_TEXT, engine)

    unplaced = bench.request(variation, None, 7)
    placed = bench.request(variation, engine, 7)
    assert (unplaced["model"], placed["model"]) == ("‹model›", engine)
    assert "‹vignette›" in str(placed["messages"])
    assert placed["seed"] == 7
    with pytest.raises(ValueError, match="not an engine"):
        _ = bench.served(variation.configuration.digest)


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


def test_a_fork_is_a_new_configuration_and_an_edit_a_new_version_of_one_s_own(
    bench: Bench,
) -> None:
    engine = bench.endpoint(QWEN)
    variation = bench.configuration(FREE_TEXT, engine)
    off = variation.set("reasoning", bench.chunk("reasoning", "off", engine), "off")
    catalog = Catalog(bench.conn)

    forked = bench.fork(off, "terse")
    again = bench.fork(off, "terse")
    assert (forked.what, again.what) == ("created", "created")
    thread = forked.variation.configuration.thread
    assert thread != again.variation.configuration.thread
    assert catalog.thread(thread).forked_from == variation.configuration.id
    assert bench.about(thread).owner == bench.person.id
    assert forked.digest == bench.skeleton(off).digest

    edited = bench.edit(thread, variation)
    assert (edited.what, edited.name) == ("a new version", "terse")
    assert bench.edit(thread, variation).what == "unchanged"
    assert [e.digest for e in catalog.history(thread)] == [
        forked.digest,
        variation.configuration.digest,
    ]

    archives = bench.thread("configuration", f"archive/{FREE_TEXT}")[0].thread
    with pytest.raises(NotFound, match=f"no configuration {archives} of yours"):
        _ = bench.edit(archives, variation)
