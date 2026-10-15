import tomllib
from pathlib import Path

import pytest

from chatddx.curation import Plan, load_cases, plan_factors
from chatddx.factors.base import resolve
from chatddx.factors.engine import RemoteEngine
from chatddx.factors.request import Compilation, Skeleton
from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import EndpointSpec, Inventory, World
from chatddx.rig import rig
from chatddx.test.world import DATA

QWEN, GPT_OSS = "Qwen/Qwen3-8B-AWQ", "openai/gpt-oss-20b"


def remote(name: str, model: str) -> str:
    return f'\n[remote_engine."{name}"]\nprovider = "example"\nmodel = "{model}"\n'


def plan(tmp_path: Path, configurations: str | None = "qwen@api", **files: str) -> Plan:
    tmp_path.mkdir(exist_ok=True)
    for name, text in files.items():
        _ = (tmp_path / name.replace("_", "-")).with_suffix(".toml").write_text(text)
    engines = tomllib.loads(files.get("engines", "")).get("remote_engine", {})
    endpoints = {
        name: EndpointSpec(engine=RemoteEngine.model_validate(body).digest)
        for name, body in engines.items()
    }
    inventory = Inventory(
        endpoints=endpoints,
        configurations=configurations if configurations in endpoints else None,
    )
    paths = (tmp_path / "engines.toml",) if engines else ()
    world = World(tmp_path, inventory, engines=paths)
    return plan_factors(tmp_path, Facts.load(BUNDLED), rig(), world)


ENGINE = remote("qwen@api", QWEN)
INTENTS = """
[prompt.case]
segments = [{ slot = "vignette" }]

[output.raw]
contract = { kind = "text" }

[sampling.recommended]
recommended = true

[reasoning.off]
level = "off"

[recipe.raw]
prompt = "case"
output = "raw"
sampling = "recommended"
reasoning = "off"
"""


def test_facts_are_planned_for_the_models_served_and_recipes_for_the_world_s_engine(
    tmp_path: Path,
) -> None:
    engines = (
        ENGINE
        + remote("gpt-oss@api", GPT_OSS)
        + remote("gemma@api", "google/gemma-3-27b-it")
    )
    planned = plan(tmp_path, engines=engines, factors=INTENTS)
    assert [(r.table, r.name) for r in planned.records] == [
        ("remote_engine", "qwen@api"),
        ("remote_engine", "gpt-oss@api"),
        ("remote_engine", "gemma@api"),
        ("facts", QWEN),
        ("facts", GPT_OSS),
        ("prompt", "case"),
        ("output", "raw"),
        ("sampling", "recommended"),
        ("reasoning", "off"),
        ("recipe", "raw"),
    ]
    assert planned.skipped == [
        "facts about google/gemma-3-27b-it: none are known, so engine.remote "
        + "gemma@api can't compile a reasoning level or a recommended sampling",
    ]
    get = planned.registry.get
    raw = planned.named("recipe", "raw")
    assert raw.compilation is not None
    compilation = resolve(get, raw.compilation, Compilation)
    assert (
        compilation.recipe.engine == planned.named("remote_engine", "qwen@api").digest
    )
    assert compilation.facts == planned.named("facts", QWEN).digest
    body = resolve(get, raw.digest, Skeleton).body
    assert body["chat_template_kwargs"] == {"enable_thinking": False}

    def on(endpoint: str | None, **files: str) -> Plan:
        return plan(tmp_path / str(endpoint), endpoint, **{"engines": engines, **files})

    nearest = on("gpt-oss@api", factors=INTENTS)
    landed = resolve(
        nearest.registry.get, nearest.named("recipe", "raw").digest, Skeleton
    )
    assert landed.body["reasoning_effort"] == "low"
    assert on("gemma@api", factors=INTENTS).skipped[-1] == (
        "recipe raw: reasoning 'off' is worked out from the facts about the engine's "
        + "model, which has none, on engine.remote gemma@api"
    )
    assert on(None, factors=INTENTS).skipped[-1] == (
        "recipe raw: the World names no endpoint configurations are made for"
    )
    old = '[sampling.recommended]\nfrom_facts = { effort = "default" }\n'
    with pytest.raises(ValueError, match="sampling: from_facts is gone"):
        _ = on("qwen@api", factors=old)
    with pytest.raises(
        ValueError, match="recipe.raw: a recipe's engine is the World's"
    ):
        _ = on("qwen@api", factors=INTENTS + 'engine = "qwen@api"\n')


NEUTRAL = """
[prompt.case]
segments = [{ slot = "vignette" }]

[output.raw]
contract = { kind = "text" }

[sampling.recommended]
recommended = true

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
        engines=ENGINE,
        factors=NEUTRAL
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
        ("facts", QWEN, None),
        ("instructions", "physician (en)", "en"),
        ("instructions", "physician (sv)", "sv"),
        ("prompt", "case", None),
        ("output", "raw", None),
        ("output", "plan (en)", "en"),
        ("sampling", "recommended", None),
        ("sampling", "greedy", None),
        ("translations", "ui (sv)", "sv"),
        ("recipe", "plan (en)", None),
        ("recipe", "plan (sv)", None),
        ("recipe", "asked (en)", None),
        ("recipe", "raw", None),
    ]
    assert planned.skipped[-1] == (
        "recipe asked (sv): its output in en needs translations in "
        + "sv, and recipe.asked names none there"
    )

    def said(name: str) -> list[str]:
        skeleton = planned.registry.get(planned.named("recipe", name).digest)
        assert isinstance(skeleton, Skeleton)
        return [str(m.content[0]) for m in skeleton.messages]

    assert said("plan (en)")[0] == "Fill in the plan."
    assert said("plan (sv)")[0] == "Fyll i planen."
    assert said("asked (en)")[0] == (
        "You are an emergency physician.\n\nFill in the plan."
    )
    compilation = planned.named("recipe", "plan (en)").compilation
    assert compilation is not None
    recipe = planned.registry.get(compilation)
    assert isinstance(recipe, Compilation) and recipe.recipe.translations is None


def test_a_fork_forks_its_origin_in_the_one_language_it_has(tmp_path: Path) -> None:
    planned = plan(
        tmp_path,
        engines=ENGINE + remote("gpt-oss@api", GPT_OSS),
        factors=NEUTRAL
        + """
[reasoning.off]
level = "off"

[recipe.plan]
prompt = "case"
output = "plan"
sampling = "recommended"
reasoning = "off"

[recipe.asked]
fork_of = "plan"
instructions = "physician"
prompt = "case"
output = "plan"
sampling = "recommended"
translations = "ui"

[recipe.greedy]
fork_of = "plan"
prompt = "case"
output = "plan"
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
    assert {r.name: r.fork_of for r in planned.records if r.table == "recipe"} == {
        "plan (en)": None,
        "asked (en)": "plan (en)",
        "asked (sv)": "plan (en)",
        "greedy (en)": "plan (en)",
    }
    assert planned.skipped == []


def test_a_fork_whose_origin_has_other_languages_is_refused(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match="recipe.asked: recipe.plan has no variant in sv to fork, and is written "
        + "in de, en",
    ):
        _ = plan(
            tmp_path,
            engines=ENGINE,
            factors=NEUTRAL
            + """
[recipe.plan]
instructions = "intro"
prompt = "case"
output = "raw"
sampling = "greedy"

[recipe.asked]
fork_of = "plan"
instructions = "physician"
prompt = "case"
output = "raw"
sampling = "greedy"
""",
            texts_en='[instructions.intro]\ntext = "Hello."\n',
            texts_de='[instructions.intro]\ntext = "Hallo."\n',
            texts_sv='[instructions.physician]\ntext = "Du är akutläkare."\n',
        )


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


LAID_OUT = """
[recipe.plan]
prompt = "case"
output = "plan"
sampling = "greedy"
translations = "ui"
appendix_layout = { before = "\\n\\nAppendices:\\n" }
"""
GROUPED = """
[translations.ui.of]
"output.plan" = [{ text = "Fill in the plan.", translation = "Fyll i planen." }]
"recipe.plan" = [{ text = "\\n\\nAppendices:\\n", translation = "\\n\\nBilagor:\\n" }]
"""


def test_translations_are_grouped_by_the_record_whose_texts_they_translate(
    tmp_path: Path,
) -> None:
    files = {"engines": ENGINE, "factors": NEUTRAL + LAID_OUT, "texts_en": ENGLISH}
    planned = plan(tmp_path, **files, texts_sv=GROUPED)
    skeleton = planned.registry.get(planned.named("recipe", "plan (sv)").digest)
    assert isinstance(skeleton, Skeleton)
    assert str(skeleton.messages[0].content[0]) == "Fyll i planen."
    assert skeleton.appendix_layout.before == "\n\nBilagor:\n"

    flat = tmp_path / "flat"
    flat.mkdir()
    entries = """
[translations.ui.entries]
"Fill in the plan." = "Fyll i planen."
"\\n\\nAppendices:\\n" = "\\n\\nBilagor:\\n"
"""
    as_entries = plan(flat, **files, texts_sv=entries)
    assert (
        as_entries.named("translations", "ui (sv)").digest
        == planned.named("translations", "ui (sv)").digest
    )


@pytest.mark.parametrize(
    ("of", "refusal"),
    [
        (
            '"output.plan" = [{ text = "Fill in the old plan.", translation = "x" }]',
            "translations.ui: output.plan holds no text 'Fill in the old plan.'",
        ),
        (
            '"output.raw" = [{ text = "Fill in the plan.", translation = "x" }]',
            "translations.ui: output.raw holds no text 'Fill in the plan.'",
        ),
        (
            '"prompt.case" = [{ text = "x", translation = "x" }]',
            "'prompt.case' names no output, toolset or recipe",
        ),
        (
            '"output.nope" = [{ text = "x", translation = "x" }]',
            "'output.nope': no output named 'nope'",
        ),
        (
            '"output.plan" = [{ text = "Fill in the plan." }]',
            "output.plan: each entry is a text and its translation",
        ),
        (
            '"output.plan" = [{ text = "Fill in the plan.", translation = "Fyll i." }, '
            + '{ text = "Fill in the plan.", translation = "Fyll i planen." }]',
            "'Fill in the plan.' is translated two ways",
        ),
    ],
)
def test_grouped_translations_are_refused_where_they_say_the_wrong_thing(
    tmp_path: Path, of: str, refusal: str
) -> None:
    files = {"engines": ENGINE, "factors": NEUTRAL + LAID_OUT, "texts_en": ENGLISH}
    with pytest.raises(ValueError, match=refusal):
        _ = plan(tmp_path, **files, texts_sv=f"[translations.ui.of]\n{of}\n")
    both = '[translations.ui]\nentries = { "Fill in the plan." = "Fyll i planen." }\n'
    with pytest.raises(ValueError, match="give its entries or its `of`, not both"):
        _ = plan(tmp_path, **files, texts_sv=both + "[translations.ui.of]\n")


def test_engines_are_the_world_s_and_only_engines_are(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError, match="remote_engine tables are the World's, in its"
    ):
        _ = plan(tmp_path, factors=ENGINE)
    with pytest.raises(
        ValueError,
        match="holds only model, local_engine, remote_engine tables, not sampling",
    ):
        _ = plan(tmp_path, factors="", engines=ENGINE + "[sampling.greedy]\n")


def test_cases_are_kept_by_language(tmp_path: Path) -> None:
    cases = load_cases(DATA)
    assert {c.language for c in cases.values()} == {"en", "sv"}
    assert (cases["crlf"].language, cases["svenska"].language) == ("en", "sv")
    assert cases["mislabeled"].language == "sv"

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
