from chatddx.bench import Bench, Carried
from chatddx.bench.configurations import keep_compilation
from chatddx.factors.base import resolve
from chatddx.factors.request import (
    Compilation,
    Instructions,
    Skeleton,
    Translations,
    untranslated,
)
from chatddx.test.world import LINES_GUIDED, NATIVE, QWEN


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
