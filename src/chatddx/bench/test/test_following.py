import pytest
from pydantic import JsonValue

from chatddx.bench import Bench, MovedOn, NotFound
from chatddx.bench.test.helpers import correct_facts, move_model, owned
from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Recipe, Skeleton
from chatddx.factors.scoring import Expectation
from chatddx.store import People, Store
from chatddx.test.world import LINES, QWEN, QWEN_ARTIFACT, QWEN_MODEL


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
def test_a_configuration_follows_its_origin_with_its_own_change_on_top(
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
    assert set(proposed.divergence.varies) == {"/recipe/reasoning"}
    assert proposed.divergence.origin_head == origin

    followed = bench.follow(mine, seen.id)
    assert (followed.what, followed.findings) == ("a new version", [])
    head = threads.head(rows, mine)
    assert (head.digest, head.based_on, head.compilation) == (
        proposed.digest,
        origin.id,
        proposed.compilation,
    )
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None and (recipe.sampling, recipe.reasoning) == (greedy, off)
    assert bench.proposal(mine) is None


def test_a_taken_expectation_follows_the_archive_s_correction(
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
    followed = bench.follow(mine, threads.head(rows, mine).id)
    assert [f.code for f in followed.findings] == ["expectation.invalid"]
    assert threads.head(rows, mine).based_on == origin.id
    assert bench.expectation(case, schema) == corrected


@pytest.mark.slow
def test_only_what_has_something_to_follow_is_followed(
    bench: Bench, archive: Bench
) -> None:
    catalog = bench.catalog
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    head = threads.head(rows, mine).id
    with pytest.raises(ValueError, match=f"configuration {mine} has nothing to follow"):
        _ = bench.follow(mine, head)
    with pytest.raises(NotFound, match=f"no configuration {theirs} of yours"):
        _ = bench.follow(theirs, threads.head(rows, theirs).id)

    greedy = bench.thread("greedy", "sampling")[0].digest
    moved = archive.variation(theirs, {"sampling": greedy})
    _ = archive.edit(theirs, threads.head(rows, theirs).id, moved)
    with pytest.raises(MovedOn, match=f"since edit {head - 1}"):
        _ = bench.follow(mine, head - 1)
    with pytest.raises(
        ValueError, match="a compiled configuration's language comes from its recipe"
    ):
        _ = bench.follow(mine, head, "en")

    gone = Entry(field=EntryField.COLLABORATOR, person=bench.person.id, present=False)
    catalog.note(Subject(thread=theirs), gone, archive.person.id)
    assert bench.proposal(mine) is None
    with pytest.raises(ValueError, match="has nothing to follow"):
        _ = bench.follow(mine, head)
    assert threads.head(rows, mine).id == head


@pytest.mark.slow
def test_a_configuration_follows_the_facts_corrected_where_they_reach_it(
    bench: Bench, archive: Bench
) -> None:
    rows = bench.rows
    mine = _own(bench)
    theirs = archive.thread(LINES, "configuration")[0].thread
    head = threads.head(rows, mine)
    assert bench.moved(mine) is None

    recommended = bench.facts.models[QWEN_MODEL].sampling.recommended
    sampled: dict[str, JsonValue] = {
        level: v.model_dump(mode="json") for level, v in recommended.items()
    }
    off: dict[str, JsonValue] = {**sampled, "off": {"temperature": 0.1}}
    _ = correct_facts(bench, QWEN_MODEL, sampling={"recommended": off})
    assert bench.moved(mine) is None

    on: dict[str, JsonValue] = {**off, "on": {"temperature": 0.2}}
    moved = correct_facts(bench, QWEN_MODEL, sampling={"recommended": on})
    found = bench.moved(mine)
    assert found is not None and archive.moved(theirs) is not None
    assert (found.about, found.model, found.refused) == (QWEN_MODEL, None, None)
    assert found.facts is not None and found.facts.head == moved
    assert found.digest is not None and found.digest != head.digest
    with pytest.raises(MovedOn, match=f"thread {mine} has moved on"):
        _ = bench.follow_moved(mine, head.id - 1)
    with pytest.raises(NotFound, match=f"no configuration {theirs} of yours"):
        _ = bench.follow_moved(theirs, threads.head(rows, theirs).id)

    followed = bench.follow_moved(mine, head.id)
    assert (followed.what, followed.edit.digest) == ("a new version", found.digest)
    assert found.compilation is not None
    assert followed.edit.compilation == found.compilation
    made = resolve(bench.store.get, found.compilation, Compilation)
    assert (made.facts, made.recipe) == (
        moved.digest,
        threads.recipe(rows, threads.head(rows, mine)),
    )
    body = resolve(bench.store.get, found.digest, Skeleton).body
    assert (body["temperature"], "top_p" in body) == (0.2, False)
    assert bench.moved(mine) is None and bench.proposal(mine) is None
    with pytest.raises(ValueError, match="compiled for nothing that has moved on"):
        _ = bench.follow_moved(mine, followed.edit.id)

    unknown: dict[str, JsonValue] = {
        "default": None,
        "on": {"chat_template_kwargs": {"enable_thinking": True}},
    }
    _ = correct_facts(bench, QWEN_MODEL, reasoning=unknown)
    refused = bench.moved(mine)
    assert refused is not None and (refused.digest, refused.compilation) == (None, None)
    assert refused.refused is not None and "no default reasoning" in refused.refused
    with pytest.raises(
        ValueError, match=f"can't follow the facts about {QWEN_MODEL}: .*no default"
    ):
        _ = bench.follow_moved(mine, followed.edit.id)


def test_a_configuration_follows_its_model_to_a_new_version(
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
    found = bench.moved(mine)
    assert found is not None and archive.moved(theirs) is not None
    assert (found.about, found.facts, found.refused) == (QWEN_MODEL, None, None)
    assert found.model is not None and found.model.head == moved
    assert found.model.digest == held != moved.digest
    assert found.digest == head.digest and found.compilation != head.compilation
    with pytest.raises(
        ValueError, match=f"no endpoint here serves model {QWEN_ARTIFACT}"
    ):
        _ = bench.at(bench.variation(mine, {"model": moved.digest}), None)

    followed = bench.follow_moved(mine, head.id)
    assert (followed.what, followed.edit.digest) == ("a new version", head.digest)
    assert followed.edit.compilation == found.compilation
    recipe = threads.recipe(rows, threads.head(rows, mine))
    assert recipe is not None and recipe.model == moved.digest
    assert resolve(bench.store.get, followed.edit.digest, Skeleton) == before
    assert bench.moved(mine) is None
    with pytest.raises(ValueError, match="compiled for nothing that has moved on"):
        _ = bench.follow_moved(mine, followed.edit.id)
