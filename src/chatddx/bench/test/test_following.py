import pytest

from chatddx.bench import Bench, MovedOn, NotFound
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.factors.base import resolve
from chatddx.factors.request import Recipe
from chatddx.factors.scoring import Expectation
from chatddx.store import People, Store
from chatddx.test.world import LINES, QWEN


@pytest.fixture
def archive(bench: Bench) -> Bench:
    found = People(bench.conn).find("archive")
    assert found is not None
    return Bench(bench.conn, found, bench.inventory, bench.facts)


def _own(bench: Bench) -> int:
    edit, about = bench.thread_by_id(
        bench.thread("configuration", LINES)[0].thread, "configuration"
    )
    assert about.owner == bench.person.id
    return edit.thread


@pytest.mark.slow
def test_a_configuration_follows_its_origin_with_its_own_change_on_top(
    bench: Bench, archive: Bench
) -> None:
    catalog, engine = bench.catalog, bench.endpoint(QWEN)
    mine = _own(bench)
    theirs = archive.thread("configuration", LINES)[0].thread
    assert bench.proposal(mine) is None

    off = bench.chunk("reasoning", "off", engine)
    greedy = bench.chunk("sampling", "greedy", engine)
    varied = bench.configuration(LINES, engine).set("reasoning", off, "off")
    seen = bench.edit(mine, varied, catalog.head(mine).id).variation.configuration
    moved = archive.variation(theirs, {"sampling": greedy})
    origin = archive.edit(
        theirs, moved, catalog.head(theirs).id
    ).variation.configuration

    proposed = bench.proposal(mine)
    assert proposed is not None and isinstance(proposed.proposal, Recipe)
    assert (proposed.proposal.sampling, proposed.proposal.reasoning) == (greedy, off)
    assert set(proposed.variation.varies) == {"/recipe/reasoning"}
    assert proposed.variation.origin_head == origin

    followed = bench.follow(mine, seen.id)
    assert (followed.what, followed.findings) == ("a new version", [])
    head = catalog.head(mine)
    assert (head.digest, head.based_on, head.compilation) == (
        proposed.digest,
        origin.id,
        proposed.compilation,
    )
    recipe = catalog.recipe(mine)
    assert recipe is not None and (recipe.sampling, recipe.reasoning) == (greedy, off)
    assert bench.proposal(mine) is None


@pytest.mark.slow
def test_a_taken_expectation_follows_the_archive_s_correction(
    bench: Bench, archive: Bench
) -> None:
    catalog, store = bench.catalog, Store(bench.conn)
    case = bench.family("noted").case
    [schema] = bench.expectation_schemas(case)
    [mine] = bench.expectation_choices([case], schema)[case]
    [(theirs, _)] = bench.shared(case, schema)
    held = resolve(store.get, theirs.digest, Expectation)
    corrected = Expectation(case=case, expectation_schema=schema, data={"x": 1})
    registry = store.load([held.digest])
    _ = store.add(registry, [registry.add(corrected)])
    origin = catalog.edit(theirs.thread, corrected.digest, archive.person.id)

    proposed = bench.proposal(mine)
    assert proposed is not None and proposed.proposal == corrected
    followed = bench.follow(mine, catalog.head(mine).id)
    assert [f.code for f in followed.findings] == ["expectation.invalid"]
    assert catalog.head(mine).based_on == origin.id
    assert bench.expectation(case, schema) == corrected


@pytest.mark.slow
def test_only_what_has_something_to_follow_is_followed(
    bench: Bench, archive: Bench
) -> None:
    catalog = bench.catalog
    mine = _own(bench)
    theirs = archive.thread("configuration", LINES)[0].thread
    head = catalog.head(mine).id
    with pytest.raises(ValueError, match=f"configuration {mine} has nothing to follow"):
        _ = bench.follow(mine, head)
    with pytest.raises(NotFound, match=f"no configuration {theirs} of yours"):
        _ = bench.follow(theirs, catalog.head(theirs).id)

    greedy = bench.chunk("sampling", "greedy", bench.endpoint(QWEN))
    moved = archive.variation(theirs, {"sampling": greedy})
    _ = archive.edit(theirs, moved, catalog.head(theirs).id)
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
    assert catalog.head(mine).id == head
