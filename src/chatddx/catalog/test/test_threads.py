import pytest

from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.catalog.test.memory import ALICE, ARCHIVE, BOB, Memory, compiled, owned
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Instructions, Sampling
from chatddx.factors.test.sample import generation_recipe, world

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
    assert (threads.origin(rows, fork.thread), threads.origin(rows, origin.thread)) == (
        origin.thread,
        None,
    )
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
