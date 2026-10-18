import pytest

from chatddx.bench import Bench
from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Reasoning, Skeleton
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.repl.shell import Repl
from chatddx.repl.test.helpers import Say, tried
from chatddx.store import Catalog, People, Rows
from chatddx.store.store import Connection
from chatddx.test.world import (
    GPT_OSS,
    GPT_OSS_ARTIFACT,
    LINES,
    MISTRAL,
    MISTRAL_ARTIFACT,
    MISTRAL_MODEL,
    NATIVE,
    NATIVE_TOOLS,
    QWEN,
    QWEN_ARTIFACT,
)


@pytest.fixture
def bob(conn: Connection) -> Person:
    return People(conn).add("bob", "Bob")


# Bob's own fork of the archive's native, as bobs-native, shared with alice when `shared`.
def bobs(conn: Connection, bob: Person, alice: Person, shared: bool) -> None:
    catalog = Catalog(conn)
    rows = Rows(conn)
    [archive] = [
        t for t in threads.find(rows, "skeleton", NATIVE) if t != alice_s(conn)
    ]
    head = threads.head(rows, archive)
    edit = catalog.create(
        head.digest,
        bob.id,
        compilation=head.compilation,
        forked_from=head.id,
        name="bobs-native",
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
    [thread] = threads.find(Rows(conn), "skeleton", NATIVE, owner=alice.id)
    return thread


def test_on_puts_its_endpoint_s_model_in_the_configuration_keeping_every_pick(
    repl: Repl, bench: Bench, say: Say
):
    _ = say("use native")
    assert tried(repl).name == NATIVE
    assert repl.prompt == f"alice {NATIVE} #7> "

    written = say("set reasoning off", f"on {GPT_OSS}")
    assert (
        f"cell: {NATIVE}+reasoning=off+model={GPT_OSS_ARTIFACT} × {GPT_OSS}" in written
    )
    assert bench.skeleton(tried(repl)).body["reasoning_effort"] == "low"

    _ = say(f"on {QWEN}")
    assert repl.prompt == f"alice {NATIVE}+reasoning=off×{QWEN} #7> "

    _ = say(f"cell native {GPT_OSS}")
    assert repl.prompt == f"alice {NATIVE}+model={GPT_OSS_ARTIFACT}×{GPT_OSS} #7> "

    _ = say(f"use {LINES}")
    assert repl.prompt == f"alice {LINES}+model={GPT_OSS_ARTIFACT}×{GPT_OSS} #7> "


def test_a_level_the_engine_s_model_refuses_is_said_until_it_is_set_otherwise(
    repl: Repl, say: Say
):
    _ = say(f"cell native {QWEN}", "set reasoning on")

    written = say(f"on {MISTRAL}")
    assert f"{MISTRAL_MODEL}: " in written and "doesn't reason" in written
    assert "set another in its place" in written and not repl.failed
    assert (
        repl.prompt
        == f"alice {NATIVE}+reasoning=on+model={MISTRAL_ARTIFACT}×{MISTRAL} #7> "
    )

    written = say("set reasoning off")
    assert "doesn't reason" not in written
    assert (
        repl.prompt
        == f"alice {NATIVE}+reasoning=off+model={MISTRAL_ARTIFACT}×{MISTRAL} #7> "
    )


def test_set_model_swaps_the_model_and_leaves_an_endpoint_serving_another(
    repl: Repl, say: Say
):
    _ = say(f"cell {LINES} {QWEN}", f"set model {GPT_OSS_ARTIFACT}")
    assert repl.cell.endpoint is None
    assert repl.prompt == f"alice {LINES}+model={GPT_OSS_ARTIFACT}×{GPT_OSS} #7> "

    _ = say(f"on {QWEN}", f"set model {QWEN_ARTIFACT}")
    assert repl.cell.named == QWEN
    assert repl.prompt == f"alice {LINES}×{QWEN} #7> "


def test_set_puts_another_chunk_in_the_cell(repl: Repl, bench: Bench, say: Say):
    written = say(f"cell {LINES} {QWEN}", "set reasoning off")

    assert repl.prompt == f"alice {LINES}+reasoning=off×{QWEN} #7> "
    assert f"cell: {LINES}+reasoning=off × {QWEN}" in written
    body = bench.skeleton(tried(repl)).body
    assert body["chat_template_kwargs"] == {"enable_thinking": False}


def test_setting_the_configuration_s_own_chunk_unsets_it(repl: Repl, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "set sampling greedy")
    assert repl.prompt == f"alice {LINES}+sampling=greedy×{QWEN} #7> "

    _ = say("set sampling recommended")
    assert repl.prompt == f"alice {LINES}×{QWEN} #7> "


@pytest.mark.slow
def test_none_takes_an_optional_part_out(repl: Repl, bench: Bench, say: Say):
    written = say(f"cell {NATIVE_TOOLS} {QWEN}", "set toolset none", "show")

    assert repl.prompt == f"alice {NATIVE_TOOLS}+toolset=none×{QWEN} #7> "
    assert f"none (set; {NATIVE_TOOLS} has lookup)" in written
    assert "tools" not in bench.skeleton(tried(repl)).body

    _ = say("set toolset lookup")
    assert repl.prompt == f"alice {NATIVE_TOOLS}×{QWEN} #7> "


def test_none_of_a_part_it_has_none_of_is_nothing_set(repl: Repl, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "set toolset none")

    assert repl.prompt == f"alice {LINES}×{QWEN} #7> "


def test_use_puts_a_configuration_in_as_it_is(repl: Repl, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "set reasoning off", "use lines")

    assert repl.prompt == f"alice {LINES}×{QWEN} #7> "


def test_set_says_what_it_can_t_set(say: Say):
    written = say("set reasoning off", f"cell {LINES} {QWEN}", "set colour red")
    written += say("set reasoning nope", "set prompt none", "set model none")
    written += say("set model nope")

    assert "the cell has no configuration to set it in" in written
    assert (
        "no part 'colour': instructions, few_shot, prompt, output, sampling, "
        + "reasoning, passthrough, translations, toolset, model"
    ) in written
    assert "no reasoning 'nope' for alice" in written
    assert "a configuration always has a prompt: only instructions" in written
    assert "a configuration always has a model" in written
    assert "no model 'nope' for alice" in written


@pytest.mark.slow
def test_save_keeps_the_cell_as_a_configuration_of_one_s_own(
    repl: Repl, bench: Bench, conn: Connection, say: Say
):
    _ = say(f"cell {LINES} {QWEN}")
    origin = tried(repl).configuration
    written = say("set reasoning off", "save quiet")

    assert "saved as quiet: created" in written
    assert repl.prompt == f"alice quiet×{QWEN} #7> "

    rows = Rows(conn)
    [thread] = threads.find(rows, "skeleton", "quiet", owner=bench.person.id)
    assert origin is not None
    assert threads.thread(rows, thread).forked_from == origin.id
    head = threads.head(rows, thread)
    assert head.compilation is not None
    recipe = resolve(bench.store.get, head.compilation, Compilation).recipe
    assert recipe.reasoning is not None
    reasoning = resolve(bench.store.get, recipe.reasoning, Reasoning)
    assert reasoning.level == "off"
    assert resolve(bench.store.get, head.digest, Skeleton).body[
        "chat_template_kwargs"
    ] == {"enable_thinking": False}

    assert "quiet" in repl.completions()["configuration"]
    assert f"cell: quiet × {QWEN}" in say("use quiet")
    assert f"cell: quiet × {QWEN}" in say("use alice/quiet")


@pytest.mark.slow
def test_saving_again_is_a_new_version_or_nothing(
    bench: Bench, conn: Connection, say: Say
):
    written = say(
        f"cell {LINES} {QWEN}",
        "save mine",
        "save mine",
        "set reasoning on",
        "save mine",
    )

    assert "saved as mine: created" in written
    assert "saved as mine: unchanged" in written
    assert "saved as mine: a new version" in written
    rows = Rows(conn)
    [thread] = threads.find(rows, "skeleton", "mine", owner=bench.person.id)
    assert len(threads.history(rows, thread)) == 2


def test_save_says_what_it_can_t_save(say: Say):
    assert "the cell has no configuration to save" in say("save nothing")


def test_one_s_own_configuration_shadows_the_archive_s(
    repl: Repl, bench: Bench, say: Say
):
    _ = say(f"use {NATIVE}")
    assert bench.thread(tried(repl).configuration.thread)[1].owner == bench.person.id

    _ = say(f"use archive/{NATIVE}")
    assert bench.thread(tried(repl).configuration.thread)[1].owner != bench.person.id
    assert repl.prompt == f"alice archive/{NATIVE} #7> "


def test_another_s_configuration_is_found_where_it_is_shared(
    repl: Repl, conn: Connection, bob: Person, bench: Bench, say: Say
):
    bobs(conn, bob, bench.person, shared=True)
    written = say("use bob/bobs-native", f"on {QWEN}", "save my-native")

    assert tried(repl).name == "my-native"
    assert "saved as my-native: created" in written

    _ = say("use bobs-native")
    assert tried(repl).name == "bobs-native"


def test_another_s_configuration_isn_t_found_where_it_isn_t_shared(
    conn: Connection, bob: Person, bench: Bench, say: Say
):
    bobs(conn, bob, bench.person, shared=False)
    written = say("use bob/bobs-native", "use bobs-native")

    assert "no configuration 'bob/bobs-native' for alice" in written
    assert "no configuration 'bobs-native' for alice" in written


def test_the_cell_s_recommended_sampling_follows_its_engine_s_model(say: Say):
    written = say(f"cell {NATIVE} {QWEN}", f"on {GPT_OSS}")

    assert "facts.sampling_unmatched" not in written


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
