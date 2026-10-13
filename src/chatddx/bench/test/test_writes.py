from typing import Any

import pytest
from pydantic import ValidationError

from chatddx.bench import Bench, MovedOn, NotFound
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.factors.request import Recipe
from chatddx.factors.scoring import Expectation, Judge
from chatddx.identity import Person
from chatddx.store import Catalog
from chatddx.test.world import LINES, QWEN

pytestmark = pytest.mark.solidified

ZERO = "sha256:" + "0" * 64


def _archive_s(bench: Bench, word: str) -> tuple[int, dict[str, Any]]:
    text = word == "instructions"
    edit, _ = next(
        (e, a)
        for e, a in bench.threads(word)
        if bench.login(a.owner) == "archive"
        and (not text or bench.catalog.language_of(e.digest) is not None)
    )
    return edit.thread, bench.get(edit.digest).model_dump(mode="json")


def test_a_person_writes_a_chunk_as_a_thread_of_their_own(bench: Bench) -> None:
    catalog = bench.catalog
    _, doc = _archive_s(bench, "instructions")
    mine = bench.component({**doc, "text": "You are a careful physician."})

    made = bench.new(mine, "careful", "en")
    assert (made.what, made.findings) == ("created", [])
    thread = made.edit.thread
    about = bench.about(thread)
    assert (about.name, about.owner) == ("careful", bench.person.id)
    assert catalog.thread(thread).forked_from is None
    assert catalog.language_of(mine.digest) == "en"

    terse = bench.component({**doc, "text": "Be terse.", "v": 1})
    edited = bench.edit_component(thread, made.edit.id, terse)
    assert edited.what == "a new version"
    assert catalog.language_of(terse.digest) is None
    assert bench.edit_component(thread, edited.edit.id, terse).what == "unchanged"
    with pytest.raises(MovedOn, match=f"since edit {made.edit.id}"):
        _ = bench.edit_component(thread, made.edit.id, mine)
    assert [e.digest for e in catalog.history(thread)] == [mine.digest, terse.digest]


def test_a_person_forks_a_chunk_they_see_as_it_is_or_changed(bench: Bench) -> None:
    catalog = bench.catalog
    origin, doc = _archive_s(bench, "instructions")
    head = catalog.head(origin)
    held = catalog.language_of(head.digest)
    assert held is not None

    same = bench.fork_component(origin, "as is", language=held)
    assert catalog.thread(same.edit.thread).forked_from == head.id
    assert same.edit.digest == head.digest
    with pytest.raises(ValueError, match=f"is in {held} already"):
        _ = bench.fork_component(origin, "relabelled", language="xx")

    changed = bench.component({**doc, "text": "Think it through."})
    fork = bench.fork_component(origin, "changed", changed, "sv")
    assert fork.edit.digest == changed.digest
    assert catalog.language_of(changed.digest) == "sv"
    assert catalog.history(origin) == [head]


def test_a_write_is_refused_what_isn_t_the_person_s_to_write(
    bench: Bench, bob: Person
) -> None:
    origin, doc = _archive_s(bench, "instructions")
    _, sampling = _archive_s(bench, "sampling")
    head = bench.catalog.head(origin).id
    mine = bench.component({**doc, "text": "Mine."})

    with pytest.raises(NotFound, match=f"no instructions {origin} of yours"):
        _ = bench.edit_component(origin, head, mine)
    with pytest.raises(ValueError, match="holds chunk.instructions components, not"):
        _ = bench.fork_component(origin, "odd", bench.component(sampling))
    with pytest.raises(ValueError, match="'tool' isn't a kind a person writes"):
        _ = bench.component({"kind": "tool"})
    with pytest.raises(ValueError, match="'skeleton' isn't a kind a person writes"):
        _ = bench.component({"kind": "skeleton"})
    with pytest.raises(ValueError, match="chunk.instructions is at v1, not v2"):
        _ = bench.component({**doc, "v": 2})
    with pytest.raises(ValidationError):
        _ = bench.component({**doc, "text": 7})
    with pytest.raises(ValueError, match="chunk.sampling components have no language"):
        _ = bench.new(bench.component(sampling), "cool", "en")
    with pytest.raises(ValueError, match=f"not in the store: \\['{ZERO}'\\]"):
        _ = bench.new(bench.component({"kind": "chunk.toolset", "tools": [ZERO]}), "x")

    theirs = Catalog(bench.conn).create(bench.component(sampling).digest, bob.id)
    with pytest.raises(NotFound, match=f"no sampling {theirs.thread} for alice"):
        _ = bench.fork_component(theirs.thread, "taken")


def test_a_person_writes_expectations_and_hears_what_the_lints_say(
    bench: Bench,
) -> None:
    catalog = bench.catalog
    case = bench.family("noted").case
    [schema] = bench.expectation_schemas(case)
    [mine] = bench.expectation_choices([case], schema)[case]
    head = catalog.head(mine)
    odd = Expectation(
        case=case, expectation_schema=schema, data=["not", "an", "object"]
    )

    with pytest.raises(ValueError, match=f"in thread {mine}: edit that one"):
        _ = bench.new(odd, "second")
    with pytest.raises(ValueError, match="expectation components have no language"):
        _ = bench.edit_component(mine, head.id, odd, "en")
    edited = bench.edit_component(mine, head.id, odd)
    assert edited.what == "a new version"
    assert [f.code for f in edited.findings] == ["expectation.invalid"]
    assert bench.expectation(case, schema) == odd

    [archives] = [
        t
        for t in catalog.expectations_of(case)
        if bench.login(bench.about(t).owner) == "archive"
    ]
    with pytest.raises(ValueError, match="has their own expectation of"):
        _ = bench.fork_component(archives, "theirs")
    catalog.note(Subject(thread=mine), Entry(field=EntryField.DELETED), bench.person.id)
    fork = bench.fork_component(archives, "theirs, mended", odd)
    assert catalog.thread(fork.edit.thread).forked_from == catalog.head(archives).id
    assert bench.expectation(case, schema) == odd


def test_a_recipe_of_the_person_s_making_is_compiled_into_a_configuration(
    bench: Bench,
) -> None:
    catalog, engine = bench.catalog, bench.endpoint(QWEN)
    recipe = Recipe(
        instructions=bench.chunk("instructions", "clinician (en)"),
        few_shot=bench.chunk("few_shot", "worked-example (en)"),
        prompt=bench.chunk("prompt", "case"),
        output=bench.chunk("output", "lines (en)"),
        sampling=bench.chunk("sampling", "greedy"),
        reasoning=bench.chunk("reasoning", "off", engine),
    )

    made = bench.new(recipe, "my own")
    assert (made.what, made.findings) == ("created", [])
    thread = made.edit.thread
    assert catalog.thread(thread).forked_from is None
    assert catalog.recipe(thread) == recipe
    assert made.edit.compilation is not None
    assert catalog.language_of(made.edit.digest) == "en"
    found = bench.configuration("my own", engine)
    assert found.configuration == made.edit
    messages = bench.request(found, engine, 7)["messages"]
    assert isinstance(messages, list) and len(messages) == 4


def test_a_recipe_is_refused_what_doesn_t_compile(bench: Bench) -> None:
    prompt = bench.chunk("prompt", "case")
    output = bench.chunk("output", "lines (en)")
    sampling = bench.chunk("sampling", "greedy")
    recipe = Recipe(prompt=prompt, output=output, sampling=sampling)

    with pytest.raises(ValueError, match=f"{output} isn't a stored chunk of prompt"):
        _ = bench.new(recipe.model_copy(update={"prompt": output}), "x")
    with pytest.raises(ValueError, match=f"{ZERO} isn't a stored chunk of toolset"):
        _ = bench.new(recipe.model_copy(update={"toolset": ZERO}), "x")
    with pytest.raises(ValueError, match="language comes from its recipe"):
        _ = bench.new(recipe, "x", "en")
    with pytest.raises(ValueError, match="generation prompt in a judge recipe"):
        _ = bench.new(recipe.model_copy(update={"purpose": "judge"}), "x")


def test_a_person_writes_a_judge_over_a_judge_configuration(bench: Bench) -> None:
    skeleton = bench.configuration("judge (en)").configuration.digest
    engine = bench.endpoint(QWEN)
    written = bench.new(Judge(skeleton=skeleton, engine=engine, seeds=(1, 2)), "twice")
    assert written.what == "created"
    assert [f.code for f in written.findings] == ["judge.greedy_seeds"]

    thread, _ = _archive_s(bench, "judge")
    forked = bench.fork_component(thread, "mine")
    assert (
        forked.what == "created"
        and bench.about(forked.edit.thread).owner == bench.person.id
    )
    once = Judge(skeleton=skeleton, engine=engine, seeds=(3,))
    edited = bench.edit_component(forked.edit.thread, forked.edit.id, once)
    assert (edited.what, edited.edit.digest) == ("a new version", once.digest)

    generation = bench.configuration(LINES).configuration.digest
    with pytest.raises(ValueError, match="judge uses a generation skeleton"):
        _ = bench.new(Judge(skeleton=generation, engine=engine, seeds=(1,)), "wrong")
