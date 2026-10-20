import pytest

from chatddx.bench import Bench, Carried
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
from chatddx.test.helpers import INSTRUCTION
from chatddx.test.world import LINES, LINES_GUIDED, NATIVE, QWEN


def swedish(bench: Bench) -> dict[str, str]:
    recipe = bench.variation(LINES_GUIDED).recipe
    assert recipe is not None and recipe.translations is not None
    return resolve(bench.store.get, recipe.translations, Translations).into["sv"]


def first_message(skeleton: Skeleton) -> object:
    rendered = skeleton.render(model="m", seed=None, fills=PLACEHOLDERS)
    messages = rendered["messages"]
    assert isinstance(messages, list) and isinstance(messages[0], dict)
    return messages[0]["content"]


def test_a_configuration_is_translated_by_its_translations(bench: Bench) -> None:
    guided = bench.variation(LINES_GUIDED)
    made = bench.translation(guided, "sv")

    assert made.digest == bench.skeleton(guided, "sv").digest
    content = first_message(made)
    assert isinstance(content, str) and content.startswith(swedish(bench)[INSTRUCTION])


def test_a_text_without_an_entry_as_typed_is_sent_as_written(bench: Bench) -> None:
    typed = {t: tr for t, tr in swedish(bench).items() if t != INSTRUCTION}
    made = bench.translation(bench.variation(LINES_GUIDED), "sv", typed)

    content = first_message(made)
    assert isinstance(content, str) and content.startswith(INSTRUCTION)
    assert "Lista de tänkbara diagnoserna" in content

    lines = bench.variation(LINES)
    assert bench.translation(lines, "sv").digest == lines.configuration.digest


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


@pytest.mark.slow
def test_translations_that_leave_a_text_out_are_said_whatever_the_cases(
    bench: Bench,
) -> None:
    engine = bench.endpoint(QWEN).engine
    terse = bench.new(Instructions(text="Read the case."), "terse", language="en")
    varied = bench.variation(LINES_GUIDED, {"instructions": terse.edit.digest})
    refused = "no translation into sv for 'Read the case.'"

    def said(carried: list[Carried] | None = None) -> list[str]:
        found = bench.findings(varied, engine, 7, carried)
        return [f.message for f in found if f.code == "translations.missing"]

    assert said() == [refused]
    cases = [f.case for f in bench.families() if f.about.language == "sv"]
    n = len(cases)
    assert said(bench.languages(varied, cases)) == [
        f"{n} cases are in sv, and left out: {refused}"
    ]
    guided = bench.variation(LINES_GUIDED)
    assert not [
        f for f in bench.findings(guided, engine, 7) if f.code == "translations.missing"
    ]


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
