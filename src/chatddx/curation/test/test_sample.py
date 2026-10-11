import pytest

from chatddx.conftest import sample_plan
from chatddx.core.rig import rig
from chatddx.factors.request import Compilation, compiled

pytestmark = pytest.mark.wip


def test_the_sample_s_texts_are_english_and_free_text_guided_swedish_too() -> None:
    sample = sample_plan()
    assert {(r.table, r.name) for r in sample.records if r.language == "en"} == {
        ("output", f"{name} (en)")
        for name in (
            "management-plan",
            "management-plan-shown",
            "management-plan-prompted",
            "diagnoses",
            "diagnoses-tool",
            "free-text",
        )
    } | {
        ("toolset", "web (en)"),
        ("instructions", "clinician (en)"),
        ("few_shot", "worked-example (en)"),
    }
    assert {(r.table, r.name) for r in sample.records if r.language == "sv"} == {
        ("instructions", "clinician (sv)"),
        ("few_shot", "worked-example (sv)"),
        ("translations", "sample (sv)"),
    }
    models = ("Qwen/Qwen3-8B-AWQ", "openai/gpt-oss-20b")
    assert {r.name for r in sample.records if r.table == "recipe"} == {
        f"{name} (en, {model})"
        for name in (
            "plan",
            "plan-shown",
            "plan-prompted",
            "plan-web",
            "diagnoses",
            "diagnoses-tool",
            "free-text",
            "free-text-guided",
        )
        for model in models
    } | {f"free-text-guided (sv, {model})" for model in models}


def test_the_sample_s_translations_carry_every_recipe_into_swedish() -> None:
    sample = sample_plan()
    translations = sample.named("translations", "sample (sv)").digest
    for r in sample.records:
        if r.table != "recipe" or r.compilation is None or "(en," not in r.name:
            continue
        held = sample.registry.get(r.compilation)
        assert isinstance(held, Compilation)
        recipe = held.recipe.model_copy(update={"translations": translations})
        skeleton, _ = compiled(recipe, sample.registry.get, rig())
        assert skeleton.digest != r.digest, r.name
