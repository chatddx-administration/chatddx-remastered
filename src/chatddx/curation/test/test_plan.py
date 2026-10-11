from pathlib import Path

import pytest

from chatddx.conftest import sample_plan
from chatddx.core.rig import rig
from chatddx.curation import Plan, load_cases, plan_factors
from chatddx.curation.plan import SAMPLE
from chatddx.factors.request import Compilation, Skeleton
from chatddx.facts import BUNDLED, Facts

pytestmark = pytest.mark.solidified


def plan(tmp_path: Path, **files: str) -> Plan:
    for name, text in files.items():
        _ = (tmp_path / name.replace("_", "-")).with_suffix(".toml").write_text(text)
    return plan_factors(tmp_path, Facts.load(BUNDLED), rig())


def test_from_facts_records_follow_the_models_the_engines_serve(
    tmp_path: Path,
) -> None:
    factors = tmp_path / "factors.toml"
    _ = factors.write_text(
        """
[remote_engine."qwen@api"]
base_url = "https://api.example/v1/"
model = "Qwen/Qwen3-8B-AWQ"

[remote_engine."gemma@api"]
base_url = "https://api.example/v1/"
model = "google/gemma-3-27b-it"

[prompt.case]
segments = [{ slot = "vignette" }]

[output.raw]
contract = { kind = "text" }

[sampling.recommended]
from_facts = { effort = "default" }

[recipe.raw]
prompt = "case"
output = "raw"
sampling = "recommended"
"""
    )
    plan = plan_factors(tmp_path, Facts.load(BUNDLED), rig())
    assert [(r.table, r.name) for r in plan.records] == [
        ("remote_engine", "qwen@api"),
        ("remote_engine", "gemma@api"),
        ("prompt", "case"),
        ("output", "raw"),
        ("sampling", "recommended (Qwen/Qwen3-8B-AWQ)"),
        ("recipe", "raw (Qwen/Qwen3-8B-AWQ)"),
    ]
    assert plan.skipped == [
        "from_facts records for google/gemma-3-27b-it: the facts don't know it, served "
        + "by engine.remote gemma@api",
        "from_facts records for openai/gpt-oss-20b: no planned engine serves it",
    ]
    assert not [s for s in sample_plan().skipped if s.startswith("from_facts records")]


ENGINE = """
[remote_engine."qwen@api"]
base_url = "https://api.example/v1/"
model = "Qwen/Qwen3-8B-AWQ"
"""
NEUTRAL = """
[prompt.case]
segments = [{ slot = "vignette" }]

[output.raw]
contract = { kind = "text" }

[sampling.recommended]
from_facts = { effort = "default" }

[sampling.greedy]
temperature = 0
"""
ENGLISH = """
[instructions.physician]
text = "You are an emergency physician."

[output.plan]
contract = { kind = "text" }
guidance = "Fill in the plan."
"""


def test_texts_are_written_by_language_and_recipes_made_in_each(
    tmp_path: Path,
) -> None:
    planned = plan(
        tmp_path,
        factors=ENGINE
        + NEUTRAL
        + """
[recipe.plan]
prompt = "case"
output = "plan"
sampling = "greedy"
translations = "ui"

[recipe.asked]
instructions = "physician"
prompt = "case"
output = "plan"
sampling = "recommended"

[recipe.raw]
prompt = "case"
output = "raw"
sampling = "greedy"
""",
        texts_en=ENGLISH,
        texts_sv="""
[instructions.physician]
text = "Du är akutläkare."

[translations.ui]
entries = { "Fill in the plan." = "Fyll i planen." }
""",
    )
    assert [(r.table, r.name, r.language) for r in planned.records] == [
        ("remote_engine", "qwen@api", None),
        ("instructions", "physician (en)", "en"),
        ("instructions", "physician (sv)", "sv"),
        ("prompt", "case", None),
        ("output", "raw", None),
        ("output", "plan (en)", "en"),
        ("sampling", "recommended (Qwen/Qwen3-8B-AWQ)", None),
        ("sampling", "greedy", None),
        ("translations", "ui (sv)", "sv"),
        ("recipe", "plan (en)", None),
        ("recipe", "plan (sv)", None),
        ("recipe", "asked (en, Qwen/Qwen3-8B-AWQ)", None),
        ("recipe", "raw", None),
    ]
    assert planned.skipped[-1] == (
        "recipe asked (sv, Qwen/Qwen3-8B-AWQ): its output in en needs translations in "
        + "sv, and recipe.asked names none there"
    )

    def said(name: str) -> list[str]:
        skeleton = planned.registry.get(planned.named("recipe", name).digest)
        assert isinstance(skeleton, Skeleton)
        return [str(m.content[0]) for m in skeleton.messages]

    assert said("plan (en)")[0] == "Fill in the plan."
    assert said("plan (sv)")[0] == "Fyll i planen."
    assert said("asked (en, Qwen/Qwen3-8B-AWQ)")[0] == (
        "You are an emergency physician.\n\nFill in the plan."
    )
    compilation = planned.named("recipe", "plan (en)").compilation
    assert compilation is not None
    recipe = planned.registry.get(compilation)
    assert isinstance(recipe, Compilation) and recipe.recipe.translations is None


@pytest.mark.parametrize(
    ("files", "refusal"),
    [
        (
            {"factors": ENGLISH},
            "instructions.physician holds text, so it's written in a "
            + r"texts-<language>.toml",
        ),
        (
            {"factors": "", "texts_en": '[output.raw]\ncontract = { kind = "text" }\n'},
            "output.raw holds no text, so it belongs in factors.toml",
        ),
        (
            {
                "factors": NEUTRAL,
                "texts_en": '[prompt.case]\nsegments = ["Case: ", { slot = "vignette" }]\n',
            },
            "prompt.case is in factors.toml and texts-en.toml",
        ),
        ({"factors": 'language = "en"\n'}, r"unknown tables \['language'\]"),
        (
            {
                "factors": "",
                "texts_en": ENGLISH.replace(
                    "[output.plan]", '[output.plan]\nlanguage = "en"'
                ),
            },
            "output.plan: a text's language is the texts file it's written in",
        ),
        (
            {"factors": "", "texts_en": "[sampling.greedy]\ntemperature = 0\n"},
            r"unknown tables \['sampling'\]",
        ),
        ({"factors": "", "texts_english": ENGLISH}, "'english' is not a language tag"),
        ({"factors": "", "texts": ENGLISH}, "texts are kept in texts-<language>.toml"),
    ],
)
def test_texts_are_refused_where_they_say_the_wrong_thing(
    tmp_path: Path, files: dict[str, str], refusal: str
) -> None:
    with pytest.raises(ValueError, match=refusal):
        _ = plan(tmp_path, **files)


def test_cases_are_kept_by_language(tmp_path: Path) -> None:
    cases = load_cases(SAMPLE)
    assert len(cases) == 99
    assert sum(c.language == "sv" for c in cases.values()) == 20
    assert {c.language for c in cases.values()} == {"en", "sv"}
    assert cases["casesfromedn1"].language == "sv"
    assert cases["Dutchfall11w"].language == "en"

    case = '[case.alpha]\ntags = ["a"]\ntargets.diagnosis.pattern = "x"\n'
    _ = (tmp_path / "cases-en.toml").write_text(case)
    _ = (tmp_path / "cases-pt-BR.toml").write_text(case.replace("alpha", "beta"))
    assert {id: c.language for id, c in load_cases(tmp_path).items()} == {
        "alpha": "en",
        "beta": "pt-BR",
    }
    for name, text, refusal in [
        ("cases-sv.toml", case, "case.alpha is in cases-en.toml too"),
        ("cases.toml", case, "cases are kept in cases-<language>.toml files"),
        ("cases-svenska.toml", "", "'svenska' is not a language tag"),
        (
            "cases-sv.toml",
            '[case.gamma]\nlanguage = "sv"\n',
            r"case.gamma: unknown keys \['language'\]",
        ),
    ]:
        path = tmp_path / name
        _ = path.write_text(text)
        with pytest.raises(ValueError, match=refusal):
            _ = load_cases(tmp_path)
        path.unlink()
