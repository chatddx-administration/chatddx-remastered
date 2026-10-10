import pytest

from chatddx.bench import Bench
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Reasoning, Skeleton
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import FREE_TEXT, GPT_OSS, PLAN, QWEN, Say, tried
from chatddx.store import Catalog, People
from chatddx.store.store import Connection

pytestmark = pytest.mark.wip


@pytest.fixture
def bob(conn: Connection) -> Person:
    return People(conn).add("bob", "Bob")


# Bob's own fork of the archive's plan, as bobs-plan, shared with alice when `shared`.
def bobs(conn: Connection, bob: Person, alice: Person, shared: bool) -> None:
    catalog = Catalog(conn)
    [archive] = [t for t in catalog.find("skeleton", PLAN) if t != alice_s(conn)]
    head = catalog.head(archive)
    edit = catalog.create(
        head.digest,
        bob.id,
        compilation=head.compilation,
        forked_from=head.id,
        name="bobs-plan",
    )
    if shared:
        catalog.note(
            Subject(thread=edit.thread),
            Entry(field=EntryField.COLLABORATOR, person=alice.id),
            bob.id,
        )


def alice_s(conn: Connection) -> int:
    alice = People(conn).find("alice")
    assert alice is not None
    [thread] = Catalog(conn).find("skeleton", PLAN, owner=alice.id)
    return thread


def test_a_per_model_configuration_is_picked_by_the_endpoint(repl: Repl, say: Say):
    written = say("use plan")

    assert (
        f"no configuration 'plan' for alice; per model: {PLAN}, "
        + "plan (en, openai/gpt-oss-20b), picked by the endpoint in the cell"
    ) in written
    assert repl.cell.variation is None

    _ = say(f"on {QWEN}", "use plan")
    assert tried(repl).name == PLAN

    _ = say(f"cell plan {GPT_OSS}")
    assert tried(repl).name == "plan (en, openai/gpt-oss-20b)"


def test_set_puts_another_chunk_in_the_cell(repl: Repl, bench: Bench, say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "set reasoning off")

    assert repl.prompt == f"alice {FREE_TEXT}+reasoning=off×{QWEN} #7> "
    assert f"cell: {FREE_TEXT}+reasoning=off × {QWEN}" in written
    body = bench.skeleton(tried(repl)).body
    assert body["chat_template_kwargs"] == {"enable_thinking": False}


def test_setting_the_configuration_s_own_chunk_unsets_it(repl: Repl, say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "set sampling greedy")
    assert repl.prompt == f"alice {FREE_TEXT}+sampling=greedy×{QWEN} #7> "

    _ = say("set sampling recommended")
    assert repl.prompt == f"alice {FREE_TEXT}×{QWEN} #7> "


@pytest.mark.slow
def test_none_takes_an_optional_part_out(repl: Repl, bench: Bench, say: Say):
    web = "plan-web (en, Qwen/Qwen3-8B-AWQ)"
    written = say(f"cell {web} {QWEN}", "set toolset none", "show")

    assert repl.prompt == f"alice {web}+toolset=none×{QWEN} #7> "
    assert f"none (set; {web} has web (en))" in written
    assert "tools" not in bench.skeleton(tried(repl)).body

    _ = say("set toolset web")
    assert repl.prompt == f"alice {web}×{QWEN} #7> "


def test_none_of_a_part_it_has_none_of_is_nothing_set(repl: Repl, say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "set toolset none")

    assert repl.prompt == f"alice {FREE_TEXT}×{QWEN} #7> "


def test_use_puts_a_configuration_in_as_it_is(repl: Repl, say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "set reasoning off", "use free-text")

    assert repl.prompt == f"alice {FREE_TEXT}×{QWEN} #7> "


def test_set_says_what_it_can_t_set(say: Say):
    written = say("set reasoning off", f"cell {FREE_TEXT} {QWEN}", "set colour red")
    written += say("set reasoning nope", "set prompt none")

    assert "the cell has no configuration to set it in" in written
    assert (
        "no part 'colour': instructions, few_shot, prompt, output, sampling, "
        + "reasoning, passthrough, translations, toolset"
    ) in written
    assert "no reasoning 'nope' for alice" in written
    assert "a configuration always has a prompt: only instructions" in written


@pytest.mark.slow
def test_save_keeps_the_cell_as_a_configuration_of_one_s_own(
    repl: Repl, bench: Bench, conn: Connection, say: Say
):
    _ = say(f"cell {FREE_TEXT} {QWEN}")
    origin = tried(repl).configuration
    written = say("set reasoning off", "save quiet")

    assert "saved as quiet: created" in written
    assert repl.prompt == f"alice quiet×{QWEN} #7> "

    catalog = Catalog(conn)
    [thread] = catalog.find("skeleton", "quiet", owner=bench.person.id)
    assert origin is not None
    assert catalog.thread(thread).forked_from == origin.id
    head = catalog.head(thread)
    assert head.compilation is not None
    recipe = resolve(bench.get, head.compilation, Compilation).recipe
    assert recipe.reasoning is not None
    reasoning = resolve(bench.get, recipe.reasoning, Reasoning)
    assert reasoning.chat_template_kwargs == {"enable_thinking": False}
    assert resolve(bench.get, head.digest, Skeleton).body["chat_template_kwargs"] == {
        "enable_thinking": False
    }

    assert "quiet" in repl.completions()["configuration"]
    assert f"cell: quiet × {QWEN}" in say("use quiet")
    assert f"cell: quiet × {QWEN}" in say("use alice/quiet")


def test_saving_again_is_a_new_version_or_nothing(
    bench: Bench, conn: Connection, say: Say
):
    written = say(
        f"cell {FREE_TEXT} {QWEN}",
        "save mine",
        "save mine",
        "set reasoning on",
        "save mine",
    )

    assert "saved as mine: created" in written
    assert "saved as mine: unchanged" in written
    assert "saved as mine: a new version" in written
    catalog = Catalog(conn)
    [thread] = catalog.find("skeleton", "mine", owner=bench.person.id)
    assert len(catalog.history(thread)) == 2


def test_save_says_what_it_can_t_save(say: Say):
    assert "the cell has no configuration to save" in say("save nothing")


def test_one_s_own_configuration_shadows_the_archive_s(
    repl: Repl, bench: Bench, say: Say
):
    _ = say(f"use {PLAN}")
    assert bench.about(tried(repl).configuration.thread).owner == bench.person.id

    _ = say(f"use archive/{PLAN}")
    assert bench.about(tried(repl).configuration.thread).owner != bench.person.id
    assert repl.prompt == f"alice archive/{PLAN} #7> "


def test_another_s_configuration_is_found_where_it_is_shared(
    repl: Repl, conn: Connection, bob: Person, bench: Bench, say: Say
):
    bobs(conn, bob, bench.person, shared=True)
    written = say("use bob/bobs-plan", f"on {QWEN}", "save my-plan")

    assert tried(repl).name == "my-plan"
    assert "saved as my-plan: created" in written

    _ = say("use bobs-plan")
    assert tried(repl).name == "bobs-plan"


def test_another_s_configuration_isn_t_found_where_it_isn_t_shared(
    conn: Connection, bob: Person, bench: Bench, say: Say
):
    bobs(conn, bob, bench.person, shared=False)
    written = say("use bob/bobs-plan", "use bobs-plan")

    assert "no configuration 'bob/bobs-plan' for alice" in written
    assert "no configuration 'bobs-plan' for alice" in written


def test_the_cell_warns_when_its_configuration_was_made_for_another_model(say: Say):
    written = say(f"cell plan {QWEN}")

    assert "facts.sampling_unmatched" not in written

    written = say(f"on {GPT_OSS}")

    assert "[warning] facts.sampling_unmatched" in written
    assert "not for openai/gpt-oss-20b" in written


def test_an_endpoint_whose_engine_isn_t_stored_is_refused(
    bench: Bench, world: Inventory, say: Say
):
    ghost = world.endpoints[QWEN].model_copy(update={"engine": "sha256:" + "0" * 64})
    bench.inventory = world.model_copy(
        update={"endpoints": {**world.endpoints, "ghost@nowhere": ghost}}
    )
    written = say("on ghost@nowhere")

    assert (
        "endpoint 'ghost@nowhere' serves engine 000000, which isn't in the store"
        in (written)
    )
