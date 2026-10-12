import json
from typing import cast

import pytest
from jsonschema import validators
from pydantic import JsonValue

from chatddx.conftest import sample_plan
from chatddx.core.rig import rig
from chatddx.curation import load_cases
from chatddx.curation.plan import SAMPLE
from chatddx.factors.request import Compilation, compiled
from chatddx.inventory import DirectorySource, Inventory
from chatddx.test.world import WORLDS

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


def test_kompismoln_takes_the_sample_s_vignettes() -> None:
    kompismoln = Inventory.load(WORLDS / "kompismoln" / "inventory.toml")
    assert kompismoln.sources["sample"] == DirectorySource(
        name="sample", path=(WORLDS / "sample" / "vignettes").resolve()
    )


TARGETS_SCHEMA = json.loads((SAMPLE / "schemas" / "targets.json").read_text())


def test_the_targets_schema_takes_the_old_chatddx_s_target_kinds() -> None:
    valid = validators.validator_for(TARGETS_SCHEMA)(TARGETS_SCHEMA).is_valid
    pneumonia: JsonValue = {"pattern": "pneumonia"}
    assert valid({"diagnosis": pneumonia})
    assert valid({"diagnosis": {"text": "Community-acquired pneumonia"}})
    assert valid(
        {
            "diagnosis": {"text": "Pneumonia", "pattern": "pneumonia"},
            "warning": False,
            "dont_miss": {"pattern": "pulmonary embolism"},
        }
    )
    invalid_targets: list[JsonValue] = [
        {"diagnosis": False},
        {"diagnosis": pneumonia, "dont_miss": False},
        {"diagnosis": {}},
        {"diagnosis": {"pattern": ""}},
        {"diagnosis": pneumonia, "critical": pneumonia},
    ]
    for invalid in invalid_targets:
        assert not valid(invalid), invalid


def test_a_case_s_notes_keep_their_author_language_comment_and_answer() -> None:
    valid = validators.validator_for(TARGETS_SCHEMA)(TARGETS_SCHEMA).is_valid
    note: dict[str, JsonValue] = {
        "author": "Olof",
        "language": "sv",
        "comment": "Chock.",
    }
    pneumonia: JsonValue = {"pattern": "pneumonia"}
    assert valid({"diagnosis": pneumonia, "notes": [note]})
    assert valid({"diagnosis": pneumonia, "notes": [note | {"answer": "Rundodla."}]})
    invalid_notes: list[JsonValue] = [
        [],
        [{k: v for k, v in note.items() if k != "author"}],
        [note | {"language": "Swedish"}],
        [note | {"comment": ""}],
        [note | {"answer": ""}],
        [note | {"date": "2026-09-28"}],
    ]
    for notes in invalid_notes:
        assert not valid({"diagnosis": pneumonia, "notes": notes}), notes


def test_the_sample_holds_olof_s_notes_on_three_cases_as_written() -> None:
    cases = load_cases(SAMPLE)
    valid = validators.validator_for(TARGETS_SCHEMA)(TARGETS_SCHEMA).is_valid
    assert all(valid(case.targets) for case in cases.values())
    noted = {
        id: case.targets["notes"]
        for id, case in cases.items()
        if isinstance(case.targets, dict) and "notes" in case.targets
    }
    assert sorted(noted) == ["Dutchfall11w", "Dutchfall1w", "casesfromedn1"]
    for id, notes in noted.items():
        assert isinstance(notes, list) and len(notes) == 1
        [note] = notes
        assert isinstance(note, dict)
        assert (note["author"], note["language"]) == ("Olof", "sv")
        assert ("answer" in note) == (id != "Dutchfall1w")
    [eleven] = cast(list[dict[str, str]], noted["Dutchfall11w"])
    assert eleven["comment"].startswith("identifiera tecken på prechock eller chock")
    assert eleven["answer"].endswith("påbörja empirisk bredspektrumantibiotika.")
