from pathlib import Path

import pytest

from chatddx.conftest import sample_plan
from chatddx.core.rig import rig
from chatddx.curation import load_cases, plan_factors
from chatddx.curation.plan import SAMPLE
from chatddx.facts import BUNDLED, Facts


def plan(tmp_path: Path, text: str) -> list[tuple[str, str, str | None]]:
    factors = tmp_path / "factors.toml"
    _ = factors.write_text(text)
    planned = plan_factors(factors, Facts.load(BUNDLED), rig())
    return [(r.table, r.name, r.language) for r in planned.records]


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
    plan = plan_factors(factors, Facts.load(BUNDLED), rig())
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


GUIDED = """
[output.plan]
contract = { kind = "text" }
guidance = "Fill in the plan."
"""


def test_a_record_that_holds_text_has_a_language_its_own_or_its_file_s(
    tmp_path: Path,
) -> None:
    assert plan(
        tmp_path,
        'language = "en"\n'
        + GUIDED
        + """
[output.plan-sv]
language = "sv"
contract = { kind = "text" }
guidance = "Fyll i planen."

[output.raw]
contract = { kind = "text" }

[prompt.case]
segments = [{ slot = "vignette" }]

[sampling.greedy]
temperature = 0
""",
    ) == [
        ("prompt", "case", None),
        ("output", "plan", "en"),
        ("output", "plan-sv", "sv"),
        ("output", "raw", None),
        ("sampling", "greedy", None),
    ]
    sample = sample_plan()
    assert {(r.table, r.name) for r in sample.records if r.language == "en"} == {
        ("output", name)
        for name in (
            "management-plan",
            "management-plan-shown",
            "management-plan-prompted",
            "diagnoses",
            "diagnoses-tool",
            "free-text",
        )
    } | {("toolset", "web")}
    assert {r.language for r in sample.records} == {"en", None}


@pytest.mark.parametrize(
    ("text", "refusal"),
    [
        (GUIDED, "output.plan: it holds text, so it needs a language"),
        (
            '[output.raw]\nlanguage = "en"\ncontract = { kind = "text" }\n',
            "output.raw: it holds no text, so it has no language",
        ),
        (
            '[sampling.greedy]\nlanguage = "en"\ntemperature = 0\n',
            "sampling.greedy: sampling records have no language",
        ),
        ('language = "english"\n' + GUIDED, "'english' is not a language tag"),
        (
            GUIDED.replace("[output.plan]", '[output.plan]\nlanguage = "en_GB"'),
            "output.plan: 'en_GB' is not a language tag",
        ),
        (
            'language = "en"\n'
            + GUIDED
            + '[prompt.case]\nsegments = [{ slot = "vignette" }]\n\n'
            + '[recipe.plan]\nlanguage = "en"\nprompt = "case"\noutput = "plan"\n',
            "recipe.plan: a recipe's language comes from its chunks",
        ),
    ],
)
def test_a_language_is_refused_where_it_says_nothing_or_isn_t_one(
    tmp_path: Path, text: str, refusal: str
) -> None:
    with pytest.raises(ValueError, match=refusal):
        _ = plan(tmp_path, text)


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
