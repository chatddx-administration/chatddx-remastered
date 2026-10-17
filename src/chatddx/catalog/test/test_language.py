import pytest

from chatddx.catalog import Entry, EntryField, Subject, language, threads
from chatddx.catalog.test.memory import Memory, compiled
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.request import (
    Prompt,
    Slot,
    Translations,
    compile_request,
    texts,
)
from chatddx.factors.scoring import Judge, Scoring
from chatddx.factors.test.sample import generation_recipe, world


def test_a_request_is_in_the_language_its_parts_agree_on() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    base = generation_recipe(reg)
    plan = compiled(reg, base)
    assert base.instructions is not None
    for part in (base.instructions, base.prompt):
        rows.set_language(part, "en")
    assert language.language_of(rows, plan.skeleton) is None
    rows.set_language(base.output, "en")
    assert language.language_of(rows, plan.skeleton) == "en"
    assert language.language_of(rows, ids["trial"]) == "en"

    needed = [t for part in texts(base, reg.get).values() for t in part]
    swedish = reg.add(Translations(into={"sv": {t: f"[sv] {t}" for t in needed}}))
    recipe = base.model_copy(update={"translations": swedish})
    assert compiled(reg, recipe).skeleton == plan.skeleton
    assert language.recipe_language(rows, recipe) == "en"
    translated = compiled(reg, recipe, "sv")
    assert language.language_of(rows, translated.skeleton) == "sv"


def test_a_recipe_votes_before_it_is_compiled() -> None:
    reg = Registry()
    rows = Memory(reg)
    base = generation_recipe(reg)
    assert base.instructions is not None
    for part in (base.instructions, base.prompt, base.output):
        rows.set_language(part, "en")
    skeleton = reg.add(compile_request(base, reg.get))
    assert language.language_of(rows, skeleton) is None
    assert language.recipe_language(rows, base) == "en"


def test_every_compilation_of_a_skeleton_votes() -> None:
    reg = Registry()
    rows = Memory(reg)
    base = generation_recipe(reg)
    plan = compiled(reg, base)
    assert base.instructions is not None
    for part in (base.instructions, base.prompt, base.output):
        rows.set_language(part, "en")
    vignette, appendices = Slot(slot="vignette"), Slot(slot="appendices")
    split = reg.add(
        Prompt(segments=("Case:", "\n", vignette, appendices, "\n\nDifferential?"))
    )
    assert compiled(reg, base.model_copy(update={"prompt": split})).skeleton == (
        plan.skeleton
    )
    assert language.language_of(rows, plan.skeleton) == "en"
    needed = [t for part in texts(base, reg.get).values() for t in part]
    unchanged = reg.add(Translations(into={"sv": {t: t for t in needed}}))
    retold = compiled(reg, base.model_copy(update={"translations": unchanged}), "sv")
    assert retold.skeleton == plan.skeleton
    assert language.language_of(rows, plan.skeleton) is None


def test_an_edit_is_in_the_language_of_its_own_recipe() -> None:
    reg = Registry()
    rows = Memory(reg)
    base = generation_recipe(reg)
    plan = compiled(reg, base)
    assert base.instructions is not None
    for part in (base.instructions, base.prompt, base.output):
        rows.set_language(part, "en")
    needed = [t for part in texts(base, reg.get).values() for t in part]
    unchanged = reg.add(Translations(into={"sv": {t: t for t in needed}}))
    retold = compiled(reg, base.model_copy(update={"translations": unchanged}), "sv")
    assert retold.skeleton == plan.skeleton

    english = rows.start(plan.skeleton, compilation=plan.digest)
    swedish = rows.start(plan.skeleton, compilation=retold.digest)
    uncompiled = rows.start(plan.skeleton)
    found = language.edit_languages(rows, [english, swedish, uncompiled])
    assert found == {english.id: "en", swedish.id: "sv", uncompiled.id: None}
    assert language.language_of(rows, plan.skeleton) is None


def test_judges_follow_their_skeleton_and_cases_their_family() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    rows.set_language(resolve(reg.get, ids["judge"], Judge).skeleton, "en")
    assert language.language_of(rows, ids["judge"]) == "en"

    expectation = resolve(reg.get, ids["scoring"], Scoring).expectations[0]
    assert language.language_of(rows, ids["case"]) is None
    _ = rows.bind(1, resolve(reg.get, ids["case"], Case).vignette)
    rows.note(Subject(family=1), Entry(field=EntryField.LANGUAGE, value="sv"))
    assert language.language_of(rows, ids["case"]) == "sv"
    assert language.language_of(rows, expectation) == "sv"


def test_many_digests_are_given_the_language_each_has_alone() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    base = generation_recipe(reg)
    plan = compiled(reg, base)
    assert base.instructions is not None
    for part in (base.instructions, base.prompt, base.output):
        rows.set_language(part, "en")
    needed = [t for part in texts(base, reg.get).values() for t in part]
    swedish = reg.add(Translations(into={"sv": {t: f"[sv] {t}" for t in needed}}))
    translated = compiled(reg, base.model_copy(update={"translations": swedish}), "sv")
    uncompiled = reg.add(
        compile_request(base.model_copy(update={"instructions": None}), reg.get)
    )
    _ = rows.bind(1, resolve(reg.get, ids["case"], Case).vignette)
    rows.note(Subject(family=1), Entry(field=EntryField.LANGUAGE, value="sv"))
    digests = {
        plan.skeleton,
        translated.skeleton,
        uncompiled,
        base.output,
        base.sampling,
        swedish,
        *ids.values(),
        "sha256:" + "0" * 64,
    }
    found = language.languages_of(rows, digests)
    assert found == {d: language.language_of(rows, d) for d in digests}
    assert {found[plan.skeleton], found[translated.skeleton], found[ids["case"]]} == {
        "en",
        "sv",
    }


def test_languages_are_refused_where_they_are_not_read() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    base = generation_recipe(reg)
    plan = compiled(reg, base)
    assert language.check_language(rows, base.prompt, "sv") == "chunk.prompt"
    with pytest.raises(ValueError, match="not a language tag"):
        _ = language.check_language(rows, base.prompt, "Swedish")
    with pytest.raises(ValueError, match="trial components have no language"):
        _ = language.check_language(rows, ids["trial"], "sv")
    translations = reg.add(Translations(into={"sv": {"Case:": "Fall:"}}))
    with pytest.raises(ValueError, match="translations components have no language"):
        _ = language.check_language(rows, translations, "sv")
    with pytest.raises(ValueError, match="comes from its recipe"):
        _ = language.check_language(rows, plan.skeleton, "sv")
    with pytest.raises(LookupError):
        _ = language.check_language(rows, "sha256:" + "9" * 64, "sv")

    swedish = Entry(field=EntryField.LANGUAGE, value="sv")
    threads.check_note(rows, Subject(family=1), swedish)
    with pytest.raises(ValueError, match="kept on its digest"):
        threads.check_note(rows, Subject(thread=1), swedish)
