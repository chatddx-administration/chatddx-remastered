from chatddx.catalog import Entry, EntryField, Subject, titles
from chatddx.catalog.test.memory import Memory, compiled
from chatddx.catalog.titles import Title, describe
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.engine import RemoteEngine, RemoteModel
from chatddx.factors.request import (
    Instructions,
    Output,
    Reasoning,
    Recipe,
    Sampling,
    Tool,
    ToolOutput,
    Toolset,
    Translations,
    texts,
)
from chatddx.factors.scoring import ExpectationSchema
from chatddx.factors.test.sample import generation_recipe, world


def titler(reg: Registry) -> Title:
    def title(digest: str) -> str:
        return describe(reg.get(digest), title)

    return title


def described(reg: Registry, recipe: Recipe) -> str:
    rows = Memory(reg)
    plan = compiled(reg, recipe)
    return titles.title(rows, rows.start(plan.skeleton, compilation=plan.digest).thread)


def test_texts_are_described_by_a_short_snippet() -> None:
    reg = Registry()
    title = titler(reg)
    brief = reg.add(Instructions(text="You  are an\nemergency physician."))
    assert title(brief) == '"You are an emergency physician."'
    long = reg.add(
        Instructions(text="You are an emergency physician on a night shift.")
    )
    assert title(long) == '"You are an emergency physician on a…"'


def test_unnamed_components_are_described_by_what_they_hold() -> None:
    reg = Registry()
    ids = world(reg)
    title = titler(reg)
    recipe = generation_recipe(reg)
    assert described(reg, recipe) == (
        '"You are an emergency physician." · "Case: {vignette}{appendices}…"'
        + " · native output: ddx · temperature 0.7, top_p 0.9, max_output_tokens 1024"
        + " · enable_thinking false · google/gemma-3-12b-it"
    )
    assert title(ids["engine"]) == "google/gemma-3-12b-it on vllm 0.24.0 (RTX 5090)"
    assert title(ids["case"]) == 'registry/c1 with "Troponin 80 ng/L."'
    assert title(ids["trial"]).endswith(
        " on google/gemma-3-12b-it on vllm 0.24.0 (RTX 5090), 1 case, 2 seeds"
    )
    assert title(ids["canaries"]) == "1 canary"
    assert title(reg.add(Sampling())) == "default sampling"
    assert title(reg.add(Sampling(recommended=True))) == "recommended sampling"
    assert (
        title(reg.add(Sampling(recommended=True, max_output_tokens=512)))
        == "recommended sampling, max_output_tokens 512"
    )
    assert title(reg.add(Reasoning(level="off"))) == "reasoning off"
    assert (
        title(reg.add(Reasoning(level="default", thinking_token_budget=64)))
        == "default reasoning, budget 64"
    )
    assert title(reg.add(Reasoning(effort="low", thinking_token_budget=512))) == (
        "effort low, budget 512"
    )
    tool = Output(
        contract=ToolOutput(name="plan", description="The plan."),
        json_schema={"type": "object", "properties": {"steps": {}, "disposition": {}}},
    )
    assert title(reg.add(tool)) == "tool plan output: steps, disposition"
    schema = reg.add(ExpectationSchema(json_schema={"title": "Targets"}))
    assert title(schema) == "Targets"
    gpt_x = reg.add(RemoteModel(provider="example", name="gpt-x"))
    assert title(gpt_x) == "gpt-x from example"
    assert title(reg.add(RemoteEngine(model=gpt_x))) == "gpt-x from example remotely"


def test_recipes_are_described_by_every_part() -> None:
    reg = Registry()
    _ = world(reg)
    title = titler(reg)
    recipe = generation_recipe(reg)
    needed = [t for part in texts(recipe, reg.get).values() for t in part]
    swedish = reg.add(Translations(into={"sv": {t: f"[sv] {t}" for t in needed}}))
    search = reg.add(
        Tool(
            name="web_search",
            description="Search the web.",
            parameters={"type": "object"},
            entry_point="chatddx_tools.web:search",
            version=1,
        )
    )
    tools = reg.add(Toolset(tools=(search,)))
    on = " · " + title(recipe.model)
    english = described(reg, recipe).removesuffix(on)
    translated = recipe.model_copy(update={"translations": swedish})
    assert described(reg, translated) == (
        english + f" · translations into sv, {len(needed)} texts" + on
    )
    with_tools = recipe.model_copy(update={"toolset": tools})
    assert described(reg, with_tools) == english + " · with web_search" + on


def test_forks_are_titled_by_what_they_change() -> None:
    reg = Registry()
    rows = Memory(reg)

    def named(edit_thread: int, name: str) -> None:
        rows.note(Subject(thread=edit_thread), Entry(field=EntryField.NAME, value=name))

    recipe = generation_recipe(reg)
    plan = compiled(reg, recipe)
    origin = rows.start(plan.skeleton, compilation=plan.digest)
    named(origin.thread, "plan")
    cool = reg.add(Sampling(temperature=0.2))
    varied = compiled(
        reg, recipe.model_copy(update={"sampling": cool, "reasoning": None})
    )
    fork = rows.start(varied.skeleton, compilation=varied.digest, forked_from=origin.id)
    assert titles.title(rows, fork.thread) == (
        "plan, no reasoning, sampling: temperature 0.2"
    )

    brief = rows.start(reg.add(Instructions(text="Be brief.")))
    named(brief.thread, "brief")
    kind = reg.add(Instructions(text="Be brief and kind to the patient."))
    kinder = rows.start(kind, forked_from=brief.id)
    assert titles.title(rows, kinder.thread) == (
        'brief, text: "Be brief and kind to the patient."'
    )
    short = rows.start(reg.add(Sampling(temperature=0.6)))
    named(short.thread, "short")
    longer = reg.add(Sampling(temperature=0.6, max_output_tokens=4096))
    assert titles.title(rows, rows.start(longer, forked_from=short.id).thread) == (
        "short, max_output_tokens: 4096"
    )


def test_titles_prefer_the_names_of_threads_that_hold_a_digest() -> None:
    reg = Registry()
    rows = Memory(reg)
    cool, greedy = reg.add(Sampling(temperature=0.5)), reg.add(Sampling(temperature=0))
    assert titles.title_of(rows, cool) == "temperature 0.5"
    named = rows.start(cool)
    rows.note(Subject(thread=named.thread), Entry(field=EntryField.NAME, value="cool"))
    assert titles.title_of(rows, cool) == "cool"
    _ = rows.save(named.thread, greedy)
    assert titles.title_of(rows, cool) == "cool (earlier)"
    assert titles.title_of(rows, greedy) == "cool"

    fork = rows.start(cool, forked_from=named.id)
    assert titles.title(rows, fork.thread) == "a fork of cool"
    assert titles.title_of(rows, cool) == "a fork of cool"
    rows.note(Subject(thread=fork.thread), Entry(field=EntryField.DELETED))
    assert titles.title_of(rows, cool) == "cool (earlier)"


def test_cases_are_titled_by_family_and_appendices() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    vignette = resolve(reg.get, ids["case"], Case).vignette
    troponin = '"Troponin 80 ng/L."'
    assert titles.title_of(rows, ids["case"]) == f"registry/c1 with {troponin}"
    _ = rows.bind(1, vignette)
    rows.note(Subject(family=1), Entry(field=EntryField.NAME, value="chest pain"))
    assert titles.title_of(rows, ids["case"]) == f"chest pain with {troponin}"
    _ = rows.bind(1, vignette.model_copy(update={"id": "c1-renamed"}))
    assert titles.title_of(rows, ids["case"]) == f"chest pain (earlier) with {troponin}"


def test_translations_are_titled_by_their_languages() -> None:
    reg = Registry()
    rows = Memory(reg)
    hello = reg.add(Translations(into={"sv": {"Hello": "Hej"}}))
    assert titles.title_of(rows, hello) == "translations into sv, 1 text"
    both = reg.add(
        Translations(
            into={"sv": {"Hello": "Hej"}, "de": {"Hello": "Hallo", "Bye": "Tschüss"}}
        )
    )
    assert titles.title_of(rows, both) == "translations into de, sv, 2 texts"
