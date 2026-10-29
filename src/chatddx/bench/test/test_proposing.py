import pytest
from pydantic import JsonValue

from chatddx.bench import Bench, MovedOn, NotFound
from chatddx.bench.test.helpers import correct_facts, move_model, owned
from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Recipe, Skeleton
from chatddx.factors.scoring import Expectation
from chatddx.store import People, Store
from chatddx.test.world import (
    GPT_OSS_ARTIFACT,
    GPT_OSS_MODEL,
    LINES,
    QWEN,
    QWEN_ARTIFACT,
    QWEN_MODEL,
)


@pytest.fixture
def archive(bench: Bench) -> Bench:
    found = People(bench.conn).find("archive")
    assert found is not None
    return Bench(bench.conn, found, bench.inventory)


def _own(bench: Bench) -> int:
    edit, about = bench.thread(
        bench.thread(LINES, "configuration")[0].thread, "configuration"
    )
    assert about.owner == bench.person.id
    return edit.thread


@pytest.mark.slow
def test_a_configuration_is_updated_from_its_origin_with_its_own_change_on_top(
    bench: Bench, archive: Bench
) -> None:
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    assert bench.proposal(mine) is None

    off = bench.thread("off", "reasoning")[0].digest
    greedy = bench.thread("greedy", "sampling")[0].digest
    varied = bench.variation(LINES).set("reasoning", off, "off")
    seen = bench.edit(mine, threads.head(rows, mine).id, varied).edit
    moved = archive.variation(theirs, {"sampling": greedy})
    origin = archive.edit(theirs, threads.head(rows, theirs).id, moved).edit

    proposed = bench.proposal(mine)
    assert proposed is not None and isinstance(proposed.proposal, Recipe)
    assert (proposed.proposal.sampling, proposed.proposal.reasoning) == (greedy, off)
    diverged = proposed.divergence
    assert diverged is not None and set(diverged.varies) == {"/recipe/reasoning"}
    assert diverged.origin_head == origin

    updated = bench.update(mine, seen.id)
    assert (updated.what, updated.findings) == ("a new version", [])
    head = threads.head(rows, mine)
    assert (head.digest, head.based_on, head.compilation) == (
        proposed.digest,
        origin.id,
        proposed.compilation,
    )
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None and (recipe.sampling, recipe.reasoning) == (greedy, off)
    assert bench.proposal(mine) is None


def test_a_taken_expectation_is_updated_to_the_archive_s_correction(
    bench: Bench, archive: Bench
) -> None:
    catalog, store = bench.catalog, Store(bench.conn)
    rows = bench.rows
    case = bench.family("noted").case
    [schema] = bench.expectation_schemas(case)
    [mine] = owned(bench, case, schema)
    [(theirs, _)] = bench.shared(case, schema)
    held = resolve(store.get, theirs.digest, Expectation)
    corrected = Expectation(case=case, expectation_schema=schema, data={"x": 1})
    registry = store.load([held.digest])
    _ = store.add(registry, [registry.add(corrected)])
    origin = catalog.edit(theirs.thread, corrected.digest, archive.person.id)

    proposed = bench.proposal(mine)
    assert proposed is not None and proposed.proposal == corrected
    updated = bench.update(mine, threads.head(rows, mine).id)
    assert [f.code for f in updated.findings] == ["expectation.invalid"]
    assert threads.head(rows, mine).based_on == origin.id
    assert bench.expectation(case, schema) == corrected


def test_only_what_has_something_to_update_is_updated(
    bench: Bench, archive: Bench
) -> None:
    catalog = bench.catalog
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    head = threads.head(rows, mine).id
    with pytest.raises(ValueError, match=f"configuration {mine} has nothing to update"):
        _ = bench.update(mine, head)
    with pytest.raises(NotFound, match=f"no configuration {theirs} of yours"):
        _ = bench.update(theirs, threads.head(rows, theirs).id)

    greedy = bench.thread("greedy", "sampling")[0].digest
    moved = archive.variation(theirs, {"sampling": greedy})
    _ = archive.edit(theirs, threads.head(rows, theirs).id, moved)
    with pytest.raises(MovedOn, match=f"since edit {head - 1}"):
        _ = bench.update(mine, head - 1)
    with pytest.raises(
        ValueError, match="a compiled configuration's language comes from its recipe"
    ):
        _ = bench.update(mine, head, "en")

    gone = Entry(field=EntryField.COLLABORATOR, person=bench.person.id, present=False)
    catalog.note(Subject(thread=theirs), gone, archive.person.id)
    assert bench.proposal(mine) is None
    with pytest.raises(ValueError, match="has nothing to update"):
        _ = bench.update(mine, head)
    assert threads.head(rows, mine).id == head


@pytest.mark.slow
def test_a_configuration_is_updated_to_the_facts_corrected_where_they_reach_it(
    bench: Bench, archive: Bench
) -> None:
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    head = threads.head(rows, mine)
    assert bench.proposal(mine) is None

    recommended = bench.facts.models[QWEN_MODEL].sampling.recommended
    sampled: dict[str, JsonValue] = {
        level: v.model_dump(mode="json") for level, v in recommended.items()
    }
    off: dict[str, JsonValue] = {**sampled, "off": {"temperature": 0.1}}
    _ = correct_facts(bench, QWEN_MODEL, sampling={"recommended": off})
    assert bench.proposal(mine) is None

    on: dict[str, JsonValue] = {**off, "on": {"temperature": 0.2}}
    moved = correct_facts(bench, QWEN_MODEL, sampling={"recommended": on})
    found = bench.proposal(mine)
    assert found is not None and archive.proposal(theirs) is not None
    assert (found.reasons, found.about, found.refused) == (("facts",), QWEN_MODEL, None)
    assert found.digest is not None and found.digest != head.digest
    with pytest.raises(MovedOn, match=f"thread {mine} has moved on"):
        _ = bench.update(mine, head.id - 1)
    with pytest.raises(NotFound, match=f"no configuration {theirs} of yours"):
        _ = bench.update(theirs, threads.head(rows, theirs).id)

    updated = bench.update(mine, head.id)
    assert (updated.what, updated.edit.digest) == ("a new version", found.digest)
    assert found.compilation is not None
    assert updated.edit.compilation == found.compilation
    made = resolve(bench.store.get, found.compilation, Compilation)
    assert (made.facts, made.recipe) == (
        moved.digest,
        threads.recipe(rows, threads.head(rows, mine)),
    )
    body = resolve(bench.store.get, found.digest, Skeleton).body
    assert (body["temperature"], "top_p" in body) == (0.2, False)
    assert bench.proposal(mine) is None
    with pytest.raises(ValueError, match="has nothing to update"):
        _ = bench.update(mine, updated.edit.id)

    unknown: dict[str, JsonValue] = {
        "default": None,
        "on": {"chat_template_kwargs": {"enable_thinking": True}},
    }
    _ = correct_facts(bench, QWEN_MODEL, reasoning=unknown)
    refused = bench.proposal(mine)
    assert refused is not None and (refused.digest, refused.compilation) == (None, None)
    assert "no default reasoning" in str(refused.refused)
    with pytest.raises(ValueError, match="can't be updated: .*no default"):
        _ = bench.update(mine, updated.edit.id)


def test_a_configuration_is_updated_to_its_model_s_new_version(
    bench: Bench, archive: Bench
) -> None:
    rows = bench.rows
    mine = _own(bench)
    head = threads.head(rows, mine)
    before = resolve(bench.store.get, head.digest, Skeleton)
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None
    held = recipe.model
    assert bench.at(bench.variation(mine), QWEN) == bench.endpoint(QWEN)

    moved = move_model(bench, QWEN_ARTIFACT, revision="moved")
    theirs = archive.thread(LINES, "configuration")[0].thread
    found = bench.proposal(mine)
    assert found is not None and archive.proposal(theirs) is not None
    assert (found.reasons, found.about, found.refused) == (("model",), QWEN_MODEL, None)
    assert held != moved.digest
    assert found.digest == head.digest and found.compilation != head.compilation
    with pytest.raises(
        ValueError, match=f"no endpoint here serves model {QWEN_ARTIFACT}"
    ):
        _ = bench.at(bench.variation(mine, {"model": moved.digest}), None)

    updated = bench.update(mine, head.id)
    assert (updated.what, updated.edit.digest) == ("a new version", head.digest)
    assert updated.edit.compilation == found.compilation
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None and recipe.model == moved.digest
    assert resolve(bench.store.get, updated.edit.digest, Skeleton) == before
    assert bench.proposal(mine) is None
    with pytest.raises(ValueError, match="has nothing to update"):
        _ = bench.update(mine, updated.edit.id)


@pytest.mark.slow
def test_a_world_s_switch_of_model_is_updated_all_at_once_and_named(
    bench: Bench, archive: Bench
) -> None:
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    before = set(bench.behind_own())
    assert mine not in before

    gpt_oss = bench.handle_named(GPT_OSS_ARTIFACT).weights
    switched = archive.variation(theirs, {"model": gpt_oss})
    _ = archive.edit(theirs, threads.head(rows, theirs).id, switched)
    assert mine in bench.behind_own()
    proposed = bench.proposal(mine)
    assert proposed is not None and proposed.reasons == ("origin",)
    assert proposed.divergence is not None and proposed.divergence.clashes == []
    assert proposed.remodelled == (QWEN_MODEL, GPT_OSS_MODEL)

    done = {u.thread: u for u in bench.update_all()}
    assert set(done) == before | {mine}
    assert done[mine].written is not None and done[mine].refused is None
    assert done[mine].remodelled == (QWEN_MODEL, GPT_OSS_MODEL)
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None and recipe.model == gpt_oss
    assert mine not in bench.behind_own()


@pytest.mark.slow
def test_updating_all_keeps_a_fork_s_change_where_its_origin_changed_it_too(
    bench: Bench, archive: Bench
) -> None:
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    greedy = bench.thread("greedy", "sampling")[0].digest
    near = bench.thread("near-greedy", "sampling")[0].digest
    varied = bench.variation(LINES).set("sampling", greedy, "greedy")
    _ = bench.edit(mine, threads.head(rows, mine).id, varied)
    moved = archive.variation(theirs, {"sampling": near})
    _ = archive.edit(theirs, threads.head(rows, theirs).id, moved)

    proposed = bench.proposal(mine)
    assert proposed is not None and proposed.divergence is not None
    assert proposed.divergence.clashes == ["/recipe/sampling"]
    assert proposed.remodelled is None
    [done] = [u for u in bench.update_all() if u.thread == mine]
    assert done.written is not None and done.refused is None
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None and recipe.sampling == greedy
