import pytest
from pydantic import JsonValue

from chatddx.catalog import Edit, Entry, EntryField, Subject, threads
from chatddx.catalog.test.memory import Memory, compiled
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case, Vignette
from chatddx.factors.request import Instructions, Sampling
from chatddx.factors.scoring import Expectation, ExpectationSchema
from chatddx.factors.test.sample import fp, generation_recipe, world

pytestmark = pytest.mark.solidified


def test_heads_and_names_skip_deleted_threads() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    kept, dropped = rows.start(ids["trial"]), rows.start(ids["trial"])
    for edit in (kept, dropped):
        rows.note(
            Subject(thread=edit.thread), Entry(field=EntryField.NAME, value="baseline")
        )
    rows.note(Subject(thread=dropped.thread), Entry(field=EntryField.DELETED))
    assert threads.heads(rows, "trial") == [kept]
    assert threads.heads(rows, "trial", deleted=True) == [dropped]
    assert threads.find(rows, "trial", "baseline") == [kept.thread]
    with pytest.raises(LookupError):
        _ = threads.history(rows, 99)


def test_forks_vary_their_base_and_follow_it_on_request() -> None:
    reg = Registry()
    rows = Memory(reg)
    recommended, longer, cooler, cooler_longer = (
        reg.add(Sampling(temperature=0.6, top_p=0.95)),
        reg.add(Sampling(temperature=0.6, top_p=0.95, max_output_tokens=4096)),
        reg.add(Sampling(temperature=0.7, top_p=0.95)),
        reg.add(Sampling(temperature=0.7, top_p=0.95, max_output_tokens=4096)),
    )
    origin = rows.start(recommended)
    fork = rows.start(longer, forked_from=origin.id)
    assert threads.forks(rows, origin.thread) == [fork.thread]
    varied = threads.variation(rows, fork.thread)
    assert varied is not None
    assert (varied.varies, varied.moved) == (
        {"/max_output_tokens": (None, 4096)},
        False,
    )
    assert threads.proposal(rows, fork.thread) is None

    moved = rows.save(origin.thread, cooler)
    assert threads.proposal(rows, fork.thread) == reg.get(cooler_longer)
    threads.check_based_on(rows, fork.thread, moved.id)
    with pytest.raises(ValueError, match="origin"):
        threads.check_based_on(rows, fork.thread, fork.id)
    _ = rows.save(fork.thread, cooler_longer, based_on=moved.id)
    varied = threads.variation(rows, fork.thread)
    assert varied is not None
    assert (varied.base, varied.moved) == (moved, False)


def test_behind_names_every_thread_that_moved_on() -> None:
    reg = Registry()
    rows = Memory(reg)
    recipe = generation_recipe(reg)
    plan = compiled(reg, recipe)
    assert recipe.instructions is not None
    shared = rows.start(recipe.instructions)
    forked = rows.start(recipe.instructions, forked_from=shared.id)
    skeleton = rows.start(plan.skeleton, compilation=plan.digest)
    assert threads.behind(rows, skeleton.thread) == []

    one = rows.save(
        shared.thread, reg.add(Instructions(text="You are a cardiologist."))
    )
    two = rows.save(forked.thread, reg.add(Instructions(text="You are a surgeon.")))
    assert [(b.path, b.head) for b in threads.behind(rows, skeleton.thread)] == [
        ("/recipe/instructions", one),
        ("/recipe/instructions", two),
    ]
    rows.note(Subject(thread=forked.thread), Entry(field=EntryField.DELETED))
    assert [b.head for b in threads.behind(rows, skeleton.thread)] == [one]


ALICE, BOB, ARCHIVE = 1, 2, 3


def owned(rows: Memory, edit: Edit, owner: int, *shared_with: int) -> Edit:
    subject = Subject(thread=edit.thread)
    rows.note(subject, Entry(field=EntryField.OWNER, person=owner))
    for person in shared_with:
        rows.note(subject, Entry(field=EntryField.COLLABORATOR, person=person))
    return edit


def test_a_person_sees_the_live_threads_they_own_or_share() -> None:
    reg = Registry()
    trial = world(reg)["trial"]
    rows = Memory(reg)
    archive = owned(rows, rows.start(trial), ARCHIVE, ALICE)
    _ = owned(rows, rows.start(trial), BOB)
    mine = owned(rows, rows.start(trial), ALICE)
    gone = owned(rows, rows.start(trial), ALICE)
    rows.note(Subject(thread=gone.thread), Entry(field=EntryField.DELETED))
    seen = threads.visible(rows, "trial", ALICE)
    assert [(e, a.owner) for e, a in seen] == [(archive, ARCHIVE), (mine, ALICE)]


def test_a_case_is_scored_against_a_person_s_own_expectation_else_a_shared_one() -> (
    None
):
    reg = Registry()
    case = world(reg)["case"]
    schema = reg.add(ExpectationSchema(json_schema={"type": "object"}))
    other_schema = reg.add(ExpectationSchema(json_schema={"type": "array"}))

    def expecting(*ddx: str, under: str = schema) -> str:
        data: JsonValue = {"ddx": list(ddx)}
        return reg.add(Expectation(case=case, expectation_schema=under, data=data))

    rows = Memory(reg)
    archive = owned(rows, rows.start(expecting("ACS")), ARCHIVE, ALICE)
    _ = owned(rows, rows.start(expecting("PE")), BOB)
    _ = owned(rows, rows.start(expecting("PE", under=other_schema)), ALICE)
    assert threads.expectation_for(rows, case, ALICE, schema) == archive.digest
    assert threads.expectation_for(rows, case, BOB, other_schema) is None

    fork = owned(rows, rows.start(archive.digest, forked_from=archive.id), ALICE)
    assert threads.expectation_for(rows, case, ALICE, schema) == fork.digest
    mine = rows.save(fork.thread, expecting("ACS", "dissection"))
    assert threads.expectation_for(rows, case, ALICE, schema) == mine.digest

    rows.note(Subject(thread=fork.thread), Entry(field=EntryField.DELETED))
    _ = owned(rows, rows.start(expecting("aortic dissection")), BOB, ALICE)
    with pytest.raises(LookupError, match="expectations to choose from, in threads"):
        _ = threads.expectation_for(rows, case, ALICE, schema)


def test_expectations_are_picked_for_several_cases_at_once() -> None:
    reg = Registry()
    case = world(reg)["case"]
    cough, rash = (
        reg.add(Case(vignette=Vignette(source="registry", id=id, fingerprint=fp(id))))
        for id in ("c2", "c3")
    )
    schema = reg.add(ExpectationSchema(json_schema={"type": "object"}))

    def expecting(of: str, *ddx: str) -> str:
        data: JsonValue = {"ddx": list(ddx)}
        return reg.add(Expectation(case=of, expectation_schema=schema, data=data))

    rows = Memory(reg)
    shared = owned(rows, rows.start(expecting(case, "ACS")), ARCHIVE, ALICE)
    _ = owned(rows, rows.start(expecting(cough, "asthma")), ARCHIVE, ALICE)
    mine = owned(rows, rows.start(expecting(cough, "pneumonia")), ALICE)
    assert threads.expectations_for(rows, [case, cough, rash], ALICE, schema) == {
        case: shared.digest,
        cough: mine.digest,
        rash: None,
    }

    pe = owned(rows, rows.start(expecting(case, "PE")), BOB, ALICE)
    croup = owned(rows, rows.start(expecting(cough, "croup")), ALICE)
    with pytest.raises(LookupError, match=f"case {cough} has expectations to choose"):
        _ = threads.expectations_for(rows, [rash, cough, case], ALICE, schema)
    assert threads.expectation_choices(rows, [case, cough, rash], ALICE, schema) == {
        case: {shared.thread: shared.digest, pe.thread: pe.digest},
        cough: {mine.thread: mine.digest, croup.thread: croup.digest},
        rash: {},
    }
