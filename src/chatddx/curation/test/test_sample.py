import json
from typing import cast

import pytest
from jsonschema import validators
from pydantic import JsonValue

from chatddx.core.rig import rig
from chatddx.curation import Plan, init, load_cases
from chatddx.factors.base import Fingerprint
from chatddx.factors.request import Compilation, compiled
from chatddx.inventory import DirectorySource, Inventory, World
from chatddx.store import Catalog, People
from chatddx.store.store import Connection
from chatddx.test.world import SAMPLE, WORLDS, world_plan

pytestmark = pytest.mark.wip


def sample_plan() -> Plan:
    return world_plan(WORLDS / "sample", SAMPLE)


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


def test_the_sample_world_holds_the_vignettes_at_7893656() -> None:
    source = Inventory.load(WORLDS / "sample" / "inventory.toml").listing("sample")
    assert source.sensitive
    assert source.ids() == sorted(load_cases(SAMPLE))
    for id in source.ids():
        _ = source.fetch(id).decode()
    listing = "".join(
        f"{c.vignette.id} {c.vignette.fingerprint.hex}\n" for c in source.cases()
    )
    assert (
        Fingerprint.of(listing.encode()).hex
        == "ce41d6b218347d2b792c86160969f937c6926c8bff255b8644c7159402d7028c"
    )


def test_the_sample_s_cases_are_79_english_and_20_swedish() -> None:
    cases = load_cases(SAMPLE)
    assert len(cases) == 99
    assert sum(c.language == "sv" for c in cases.values()) == 20
    assert cases["casesfromedn1"].language == "sv"
    assert cases["Dutchfall11w"].language == "en"


@pytest.mark.slow
def test_the_sample_loads_with_its_world_s_fakes(conn: Connection) -> None:
    alice = People(conn).add("alice", "Alice")
    plan = sample_plan()
    assert plan.skipped == [
        f"reasoning {effort} (openai/gpt-oss-20b): {reason}"
        for effort, reason in [
            ("off", "always reasons: vLLM rejects reasoning_effort = none for harmony"),
            ("minimal", "harmony has no minimal effort, only low, medium and high"),
            ("xhigh", "harmony has no xhigh effort, only low, medium and high"),
            ("on-budget-2048", "no thinking budget is documented for harmony"),
        ]
    ]
    world = World.load(WORLDS / "sample")
    lines = init(conn, plan, load_cases(SAMPLE), world.inventory.listing(), alice)
    fakes = ("qwen3-8b-awq@fake", "gpt-oss-20b@fake")
    assert [line for line in lines if line.startswith("[lint warning]")] == [
        *(
            f"[lint warning] model {name}: model.revision: revision 'fake' is not a "
            + "commit and can move"
            for name in fakes
        ),
        *(
            f"[lint warning] engine.local {name}: engine.closure: closure 'chatddx "
            + "fake-vllm' is not a Nix store path"
            for name in fakes
        ),
    ]
    assert not [line for line in lines if "needs repair" in line]
    catalog = Catalog(conn)
    [plan_thread] = catalog.find("skeleton", "plan (en, Qwen/Qwen3-8B-AWQ)")
    [shown] = catalog.find("skeleton", "plan-shown (en, Qwen/Qwen3-8B-AWQ)")
    variation = catalog.variation(shown)
    assert variation is not None and set(variation.varies) == {"/recipe/output"}
    assert variation.base.thread == plan_thread
