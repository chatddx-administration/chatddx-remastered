import re
from uuid import UUID

import pytest
from pydantic import JsonValue

from chatddx.bench import Ambiguous, Bench, Conflict, Graded, MovedOn, NotFound
from chatddx.bench.test.helpers import another_expectation, ran, trial
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.curation import Plan, load_cases
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation, Judge, View
from chatddx.identity import Person
from chatddx.runner.score import Grader, score_run
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection
from chatddx.test.world import (
    DATA,
    GPT_OSS,
    LINES,
    MODELS,
    NATIVE,
    QWEN,
    QWEN_MODEL,
    REMOTE,
)

pytestmark = pytest.mark.wip


def test_a_person_sees_their_own_and_shared_threads_and_families(
    conn: Connection, alice: Person, bob: Person, bench: Bench
) -> None:
    owners = {a.owner for _, a in bench.threads("configuration")}
    archive = People(conn).find("archive")
    assert archive is not None and owners == {alice.id, archive.id}

    mine, _ = bench.thread("configuration", LINES)
    assert bench.about(mine.thread).owner == alice.id
    theirs, _ = bench.thread("configuration", f"archive/{LINES}")
    assert bench.about(theirs.thread).owner == archive.id
    assert theirs.digest == mine.digest and theirs.thread != mine.thread
    with pytest.raises(NotFound, match="no configuration 'nothing' for alice"):
        _ = bench.thread("configuration", "nothing")

    families, cases = bench.families(), load_cases(DATA)
    assert len(families) == len(cases)
    assert {f.about.language for f in families} == {c.language for c in cases.values()}
    assert {f.name: f.about.tags for f in families} == {
        name: set(c.tags) for name, c in cases.items()
    }
    assert all(f.about.tags for f in families)
    bobs = Bench(conn, bob, bench.inventory, bench.facts)
    assert bobs.threads("configuration") == [] and bobs.families() == []


def test_a_case_is_found_by_its_name_or_as_owner_slash_name(bench: Bench) -> None:
    found = bench.family("noted")
    assert bench.family("archive/noted") == found
    with pytest.raises(NotFound, match="no case 'alice/noted' for alice"):
        _ = bench.family("alice/noted")
    with pytest.raises(NotFound, match="no case 'nope' for alice"):
        _ = bench.family("nope")


def test_threads_cases_and_runs_are_found_by_id_among_what_the_person_sees(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    mine, _ = bench.thread("configuration", LINES)
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

    family = bench.family("noted")
    assert bench.family_by_id(family.id) == family
    with pytest.raises(NotFound, match=f"no case {family.id} for bob"):
        _ = bobs.family_by_id(family.id)
    with pytest.raises(NotFound, match="no case 0 for alice"):
        _ = bench.family_by_id(0)

    made = trial(conn, plan, LINES, "crlf")
    own, theirs = ran(conn, alice, made), ran(conn, bob, made)
    assert bench.run_by_id(own).run == own
    with pytest.raises(NotFound, match=f"no run {theirs} of yours"):
        _ = bench.run_by_id(theirs)


def test_a_variation_is_made_from_a_configuration_s_id_and_digests(
    bench: Bench,
) -> None:
    engine = bench.endpoint(QWEN)
    named = bench.configuration(LINES, engine)
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
    lines = trial(conn, plan, LINES, "crlf", "svenska")
    native = trial(conn, plan, NATIVE, "crlf")
    first = ran(conn, alice, lines)
    second = ran(conn, alice, native)
    _ = ran(conn, bob, lines)
    gone = ran(conn, alice, native)
    Catalog(conn).note(Subject(run=gone), Entry(field=EntryField.DELETED), alice.id)

    assert [r.run for r in bench.runs()] == [second, first]
    assert bench.run().run == second
    assert bench.run(str(first)[:8]).run == first
    with pytest.raises(Ambiguous, match="2 runs of yours start with ''"):
        _ = bench.run("")
    with pytest.raises(NotFound, match="no run of yours"):
        _ = bench.run("zzz")

    assert [r.run for r in bench.reaching(lines.skeleton)] == [first]
    output = plan.named("output", "lines (en)").digest
    assert [r.run for r in bench.reaching(output)] == [first]
    [shared_case] = set(lines.cases) & set(native.cases)
    assert [r.run for r in bench.reaching(shared_case)] == [second, first]
    store = Store(conn)
    assert len(store.runs_of(lines.digest)) == 2
    assert store.finished([first, second, gone]) == {first, second, gone}


def test_a_view_of_the_whole_answer_is_offered_by_a_text_output_only(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    whole, picked = View(metric="m"), View(output="$.diagnoses[*]", metric="m")
    schema: JsonValue = {
        "type": "object",
        "properties": {"diagnoses": {"type": "array", "items": {"type": "string"}}},
    }
    assert whole.offered_by(None) and not whole.offered_by(schema)
    assert not View(output="$", metric="m").offered_by(schema)
    assert picked.offered_by(schema) and not picked.offered_by(None)

    started = bench.run(str(ran(conn, alice, trial(conn, plan, NATIVE, "crlf"))))
    assert {a.name for _, a in bench.scorers_for(started)} == {"answer", "list"}


@pytest.mark.slow
def test_a_run_is_left_to_score_until_scored_under_the_scoring_built_now(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    made = trial(conn, plan, LINES, "crlf", "svenska")
    run = ran(conn, alice, made)
    _ = ran(conn, alice, made, finished=False)
    started = bench.run(str(run))
    texts = {"lines", "whole", "judged"}
    assert {a.name for _, a in bench.scorers_for(started)} == texts

    scorer = plan.named("scorer", "lines").digest
    others = {plan.named("scorer", name).digest for name in texts - {"lines"}}
    assert set(bench.unscored(started)) == {scorer, *others}
    assert [(r.run, set(s)) for r, s in bench.outstanding()] == [
        (run, {scorer, *others})
    ]
    scoring = bench.scoring(started, scorer)
    assert scoring is not None and len(scoring.expectations) == 2
    store = Store(conn)
    registry = store.load([scorer, *scoring.expectations])
    _, findings = score_run(conn, run, scoring, registry, alice)
    assert findings == []
    assert set(bench.unscored(started)) == others
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
    assert set(bench.unscored(started)) == {scorer, *others}
    rebuilt = bench.scoring(started, scorer)
    assert rebuilt is not None and edited in rebuilt.expectations


def test_only_a_finished_score_counts_against_what_is_left_to_score(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    run = ran(conn, alice, trial(conn, plan, LINES, "crlf"))
    started = bench.run_by_id(run)
    scorer = plan.named("scorer", "lines").digest
    scoring = bench.scoring(started, scorer)
    assert scoring is not None
    registry = Store(conn).load([scorer, *scoring.expectations])

    grading = Grader(conn, None, alice).start(run, scoring, registry)
    assert scorer in bench.unscored(started)

    _ = grading.finish()
    assert scorer not in bench.unscored(started)
    assert [r.run for r in bench.scored_by(scorer)] == [run]


def test_a_case_is_held_to_the_expectation_scoring_picks(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    case = bench.family("noted").case
    schema = plan.named("expectation_schema", "targets").digest
    assert bench.expectation_schemas(case) == [schema]

    held = bench.expectation(case, schema)
    assert held is not None
    assert held.digest == Catalog(conn).expectation_for(case, alice.id, schema)

    theirs = Bench(conn, bob, bench.inventory, bench.facts)
    assert theirs.expectation_schemas(case) == []
    assert theirs.expectation(case, schema) is None

    catalog = Catalog(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [shared] = [
        t
        for t in catalog.expectations_of(case)
        if catalog.about(Subject(thread=t)).owner == archive.id
    ]
    to_bob = Entry(field=EntryField.COLLABORATOR, person=bob.id)
    catalog.note(Subject(thread=shared), to_bob, archive.id)
    assert theirs.expectation_schemas(case) == [schema]
    assert theirs.expectation(case, schema) is None


@pytest.mark.slow
def test_several_expectations_to_choose_from_are_ambiguous(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    made = trial(conn, plan, LINES, "crlf")
    [case] = made.cases
    _ = another_expectation(bench, case, {"diagnosis": {"pattern": "sepsis"}})
    [schema] = bench.expectation_schemas(case)
    scorer = plan.named("scorer", "lines").digest
    started = bench.run_by_id(ran(conn, alice, made))

    with pytest.raises(Ambiguous, match="has expectations to choose from"):
        _ = bench.expectation(case, schema)
    with pytest.raises(Ambiguous, match="has expectations to choose from"):
        _ = bench.scoring(started, scorer)

    assert scorer in bench.unscored(started)
    assert [r.run for r, _ in bench.outstanding()] == [started.run]
    [graded] = bench.score(started, [scorer])
    assert graded.score is None
    assert graded.refused and "has expectations to choose from" in graded.refused
    assert Store(conn).scores_of(started.run) == []

    family = bench.family("crlf")
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
    [held] = [
        r for r in bench.reach(variation, [family]) if r.offered and r.scorer == "whole"
    ]
    assert (held.choosing, held.missing, held.have) == ([family], [], 0)


def test_a_per_model_configuration_is_picked_by_the_engine_s_model(
    bench: Bench,
) -> None:
    with pytest.raises(NotFound) as refused:
        _ = bench.configuration("native")
    assert refused.value.per_model == tuple(sorted(f"native (en, {m})" for m in MODELS))

    variation = bench.configuration("native", bench.endpoint(QWEN))
    assert (variation.name, variation.label, variation.parts) == (NATIVE, NATIVE, {})

    with pytest.raises(NotFound) as refused:
        _ = bench.configuration("nope", bench.endpoint(QWEN))
    assert refused.value.per_model == ()


def test_a_configuration_made_in_several_languages_is_named_whole(
    bench: Bench, alice: Person
) -> None:
    engine = bench.endpoint(QWEN)
    english = bench.configuration("native", engine).configuration
    swedish = f"native (sv, {QWEN_MODEL})"
    assert swedish not in bench.names("configuration")
    _ = bench.catalog.create(english.digest, alice.id, name=swedish)
    several = (
        f"made in more than one language: {NATIVE}, {swedish}; "
        + "name one as 'native en' or 'native sv'"
    )
    with pytest.raises(Ambiguous, match=re.escape(several)):
        _ = bench.configuration("native", engine)
    assert bench.configuration(swedish, engine).name == swedish
    assert bench.configuration("native sv", engine).name == swedish
    assert bench.configuration("native (en)", engine).name == NATIVE
    with pytest.raises(NotFound) as refused:
        _ = bench.configuration("native sv")
    assert refused.value.per_model == (swedish,)
    with pytest.raises(NotFound, match="no configuration 'native fi'"):
        _ = bench.configuration("native fi", engine)


def test_a_variation_compiles_to_a_skeleton_of_its_own(bench: Bench) -> None:
    engine = bench.endpoint(QWEN)
    configuration = bench.configuration(LINES, engine)
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
    variation = bench.configuration(LINES, engine)

    unplaced = bench.request(variation, None, 7)
    placed = bench.request(variation, engine, 7)
    assert (unplaced["model"], placed["model"]) == ("‹model›", engine)
    assert "‹vignette›" in str(placed["messages"])
    assert placed["seed"] == 7
    with pytest.raises(ValueError, match="not an engine"):
        _ = bench.served(variation.configuration.digest)


def test_several_configurations_of_one_name_are_refused_a_save(bench: Bench) -> None:
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
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
    variation = bench.configuration(LINES, engine)
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

    seen = forked.variation.configuration.id
    edited = bench.edit(thread, variation, seen)
    assert (edited.what, edited.name) == ("a new version", "terse")
    now = edited.variation.configuration.id
    assert bench.edit(thread, variation, now).what == "unchanged"
    assert [e.digest for e in catalog.history(thread)] == [
        forked.digest,
        variation.configuration.digest,
    ]
    with pytest.raises(MovedOn, match=f"since edit {seen}: its head is edit {now}"):
        _ = bench.edit(thread, off, seen)

    archives = bench.thread("configuration", f"archive/{LINES}")[0].thread
    with pytest.raises(NotFound, match=f"no configuration {archives} of yours"):
        _ = bench.edit(archives, variation, now)


def _expectation_of(catalog: Catalog, case: str, owner: int) -> int:
    [thread] = [
        t
        for t in catalog.expectations_of(case)
        if catalog.about(Subject(thread=t)).owned_by(owner)
    ]
    return thread


@pytest.mark.slow
def test_a_person_takes_the_expectations_shared_with_them(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    catalog, store = Catalog(conn), Store(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    schema = plan.named("expectation_schema", "targets").digest
    crlf, noted, svenska = (bench.family(n).case for n in ("crlf", "noted", "svenska"))
    gone = Entry(field=EntryField.DELETED)
    for case in (crlf, svenska):
        own = _expectation_of(catalog, case, alice.id)
        catalog.note(Subject(thread=own), gone, alice.id)
    kept = _expectation_of(catalog, noted, alice.id)

    taken = bench.take([crlf, noted, svenska, crlf], schema)
    assert (taken.kept, taken.choosing, taken.missing) == ({noted: kept}, {}, [])
    assert set(taken.taken) == {crlf, svenska}
    origin = _expectation_of(catalog, crlf, archive.id)
    took = catalog.thread(taken.taken[crlf])
    assert took.forked_from == catalog.head(origin).id
    assert catalog.about(Subject(thread=took.id)).owner == alice.id
    held = bench.expectation(crlf, schema)
    assert held is not None and held.digest == catalog.head(origin).digest

    again = bench.take([crlf, noted, svenska], schema)
    assert again.taken == {} and set(again.kept) == {crlf, noted, svenska}

    catalog.note(Subject(thread=taken.taken[crlf]), gone, alice.id)
    head = resolve(store.get, catalog.head(origin).digest, Expectation)
    registry = store.load([head.digest])
    theirs = registry.add(
        Expectation(case=crlf, expectation_schema=schema, data={"diagnosis": "x"})
    )
    _ = store.add(registry, [theirs])
    bobs = catalog.create(theirs, bob.id).thread
    to_alice = Entry(field=EntryField.COLLABORATOR, person=alice.id)
    catalog.note(Subject(thread=bobs), to_alice, bob.id)
    assert bench.take([crlf], schema).choosing == {crlf: [origin, bobs]}
    assert set(bench.take([crlf], schema, owner="archive").taken) == {crlf}

    assert bench.take([crlf], schema, owner="bob").kept == {
        crlf: _expectation_of(catalog, crlf, alice.id)
    }
    with pytest.raises(NotFound, match="no person 'nobody'"):
        _ = bench.take([crlf], schema, owner="nobody")
    with pytest.raises(ValueError, match="isn't a stored expectation schema"):
        _ = bench.take([crlf], crlf)


def test_a_person_replaces_their_own_expectation_only_when_they_say_so(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    catalog = Catalog(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    schema = plan.named("expectation_schema", "targets").digest
    case = bench.family("noted").case
    mine = _expectation_of(catalog, case, alice.id)
    origin = _expectation_of(catalog, case, archive.id)

    with pytest.raises(
        Conflict, match=f"has their own .* in thread {mine}: replace it"
    ):
        _ = bench.take_from(origin)
    with pytest.raises(ValueError, match=f"expectation {mine} is yours already"):
        _ = bench.take_from(mine)
    with pytest.raises(NotFound, match="no expectation"):
        _ = bench.take_from(bench.threads("configuration")[0][0].thread)

    took = bench.take_from(origin, replace=True)
    assert catalog.about(Subject(thread=mine)).deleted
    assert catalog.thread(took).forked_from == catalog.head(origin).id
    assert bench.shared(case, schema)[0][0].thread == origin
    held = bench.expectation(case, schema)
    assert held is not None and held.digest == catalog.head(origin).digest


@pytest.mark.slow
def test_a_judged_scorer_applies_where_the_world_lets_its_judges_run(
    conn: Connection,
    alice: Person,
    bench: Bench,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHATDDX_TEST_REMOTE", raising=False)
    run = ran(conn, alice, trial(conn, plan, LINES, "noted"))
    started = bench.run(str(run))
    applies = {a.name for _, a in bench.scorers_for(started)}
    assert "judged" in applies and "judged-remote" not in applies
    assert plan.named("scorer", "judged-remote").digest not in bench.unscored(started)

    cleared = bench.inventory.model_copy(
        update={"cleared": bench.inventory.cleared | {REMOTE: ("test",)}}
    )
    opened = Bench(conn, alice, cleared, bench.facts)
    assert "judged-remote" in {a.name for _, a in opened.scorers_for(started)}
    [refused] = [g for g in opened.score(started) if g.name == "judged-remote"]
    assert refused.refused == (
        f"endpoint {REMOTE!r} needs the secret in $CHATDDX_TEST_REMOTE, which isn't set"
    )


def scored(graded: Graded) -> UUID:
    assert graded.score is not None
    return graded.score.started.score


def test_a_run_s_scores_are_read_the_latest_every_one_or_one_by_id(
    conn: Connection, alice: Person, bob: Person, bench: Bench, plan: Plan
) -> None:
    run = ran(conn, alice, trial(conn, plan, LINES, "crlf"))
    other = ran(conn, alice, trial(conn, plan, LINES, "svenska"))
    lines = plan.named("scorer", "lines").digest
    [first] = bench.score(bench.run_by_id(run), {lines})
    [second] = bench.score(bench.run_by_id(run), {lines})

    [latest] = bench.scores_of(run)
    assert (latest.name, scored(latest)) == ("lines", scored(second))
    every = [scored(g) for g in bench.scores_of(run, every=True)]
    assert every == [scored(second), scored(first)]
    assert scored(bench.score_of(run, scored(first))) == scored(first)
    assert bench.scorer_name(lines) == "lines"

    with pytest.raises(NotFound, match=f"no score {scored(first)} of run {other}"):
        _ = bench.score_of(other, scored(first))
    theirs = Bench(conn, bob, bench.inventory, bench.facts)
    with pytest.raises(NotFound, match=f"no run {run} of yours"):
        _ = theirs.score_of(run, scored(first))


def test_a_judge_configuration_is_looked_at_as_a_judge_and_isn_t_run(
    bench: Bench,
) -> None:
    configurations = bench.threads("configuration")
    judges = {a.name for _, a in bench.purposed(configurations, "judge")}
    generation = {a.name for _, a in bench.purposed(configurations, "generation")}
    assert f"judge-graded (en, {QWEN_MODEL})" in judges and LINES in generation
    assert not judges & generation

    variation = bench.configuration(f"judge-graded (en, {QWEN_MODEL})")
    engine = bench.endpoint(GPT_OSS)
    findings = bench.findings(variation, engine, 7, bench.families())
    judge = Judge(skeleton=variation.configuration.digest, engine=engine, seeds=(7,))
    assert {f.code for f in findings} == {
        "facts.output_note",
        "facts.sampling_unmatched",
    }
    assert {f.subject for f in findings} == {judge.digest}
    assert bench.reach(variation, bench.families()) == []

    case = bench.family("crlf").case
    with pytest.raises(ValueError, match="is a judge configuration"):
        _ = bench.start(variation, QWEN, [case], 7)
