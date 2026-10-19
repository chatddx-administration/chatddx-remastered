import pytest

from chatddx.bench import Bench
from chatddx.bench.configurations import keep_compilation
from chatddx.bench.model import PLACEHOLDERS
from chatddx.factors.base import resolve
from chatddx.factors.request import (
    Compilation,
    Instructions,
    Skeleton,
    Translations,
    untranslated,
)
from chatddx.identity import Person
from chatddx.test.world import LINES, LINES_GUIDED, NATIVE, QWEN

INSTRUCTION = (
    "You are assisting a physician in an emergency department. Read the case and give "
    + "your assessment."
)


def swedish(bench: Bench) -> dict[str, str]:
    recipe = bench.variation(LINES_GUIDED).recipe
    assert recipe is not None and recipe.translations is not None
    return resolve(bench.store.get, recipe.translations, Translations).into["sv"]


def first_message(skeleton: Skeleton) -> object:
    rendered = skeleton.render(model="m", seed=None, fills=PLACEHOLDERS)
    messages = rendered["messages"]
    assert isinstance(messages, list) and isinstance(messages[0], dict)
    return messages[0]["content"]


def test_a_configuration_s_texts_come_with_their_translations(bench: Bench) -> None:
    guided = bench.variation(LINES_GUIDED)
    made = bench.translation(guided, "sv")

    assert (made.language, made.unused) == ("en", {})
    assert list(made.texts) == ["instructions", "few_shot", "output", "appendix_layout"]
    assert dict(made.texts["instructions"]) == {
        INSTRUCTION: swedish(bench)[INSTRUCTION]
    }
    assert all(
        translation is not None for t in made.texts.values() for _, translation in t
    )
    assert made.skeleton.digest == bench.skeleton(guided, "sv").digest


def test_entries_as_typed_leave_a_text_as_written_and_an_entry_unused(
    bench: Bench,
) -> None:
    typed = {t: tr for t, tr in swedish(bench).items() if t != INSTRUCTION}
    typed["Gone since"] = "Borta sedan"
    made = bench.translation(bench.variation(LINES_GUIDED), "sv", typed)

    assert made.texts["instructions"] == [(INSTRUCTION, None)]
    assert made.unused == {"Gone since": "Borta sedan"}
    content = first_message(made.skeleton)
    assert isinstance(content, str) and content.startswith(INSTRUCTION)
    assert "Lista de tänkbara diagnoserna" in content


def test_a_configuration_without_translations_has_every_text_as_written(
    bench: Bench,
) -> None:
    lines = bench.variation(LINES)
    made = bench.translation(lines, "sv")

    assert {t for found in made.texts.values() for t in found} == {
        ("List the plausible diagnoses, one per line, most likely first.", None)
    }
    assert made.skeleton.digest == lines.configuration.digest


def test_a_translation_needs_a_recipe_and_another_language(
    bench: Bench, alice: Person
) -> None:
    guided = bench.variation(LINES_GUIDED)
    with pytest.raises(ValueError, match="lines-guided is written in en"):
        _ = bench.translation(guided, "en")
    with pytest.raises(ValueError, match="'svenska!' is not a language tag"):
        _ = bench.translation(guided, "svenska!")

    _ = bench.catalog.create(guided.configuration.digest, alice.id, name="by hand")
    with pytest.raises(ValueError, match="by hand has no recipe to translate"):
        _ = bench.translation(bench.variation("by hand"), "sv")


def test_translations_that_leave_a_text_out_are_linted_whatever_the_cases(
    bench: Bench,
) -> None:
    engine = bench.endpoint(QWEN).engine
    terse = bench.new(Instructions(text="Read the case."), "terse", language="en")
    varied = bench.variation(LINES_GUIDED, {"instructions": terse.edit.digest})

    found = {f.code: f.message for f in bench.findings(varied, engine, 7)}
    assert found["translations.incomplete"] == (
        "its translations into sv leave 1 text untranslated: 'Read the case.'"
    )

    cases = [f.case for f in bench.families() if f.about.language == "sv"]
    carried = bench.languages(varied, cases)
    codes = {f.code for f in bench.findings(varied, engine, 7, carried)}
    assert "translations.missing" in codes
    assert "translations.incomplete" not in codes

    guided = bench.variation(LINES_GUIDED)
    codes = {f.code for f in bench.findings(guided, engine, 7)}
    assert "translations.incomplete" not in codes


def test_a_translated_answer_is_told_by_its_schema_s_title_as_written(
    bench: Bench,
) -> None:
    native = bench.variation(NATIVE)
    assert native.recipe is not None
    needed = untranslated(native.recipe, bench.store.get, "sv")
    into = {"sv": {t: f"[sv] {t}" for t in needed}}
    made = bench.new(Translations(into=into), "native-sv")
    varied = bench.variation(NATIVE, {"translations": made.edit.digest})
    compilation = keep_compilation(bench, varied, "sv")
    assert compilation is not None
    translated = resolve(
        bench.store.get,
        resolve(bench.store.get, compilation, Compilation).skeleton,
        Skeleton,
    )

    schema = translated.output_schema
    assert isinstance(schema, dict) and schema["title"] == "[sv] Answer"
    assert (
        bench.answers(translated) == bench.answers(bench.skeleton(native)) == "Answer"
    )
