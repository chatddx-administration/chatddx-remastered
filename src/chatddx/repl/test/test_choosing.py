import pytest

from chatddx.bench import Bench
from chatddx.catalog import Entry, EntryField, Subject, threads
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Reasoning, Skeleton
from chatddx.identity import Person
from chatddx.repl.shell import Repl
from chatddx.repl.test.helpers import Say, by_hand, tried
from chatddx.store import Catalog, People, Rows
from chatddx.store.store import Connection
from chatddx.test.helpers import added_bob
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

__all__ = ["added_bob"]


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


def test_set_model_swaps_the_model_keeping_every_pick_and_runs_under_its_handle(
    repl: Repl, bench: Bench, say: Say
):
    _ = say("use native")
    assert tried(repl).name == NATIVE
    assert repl.prompt == f"alice {NATIVE} #7> "

    written = say("set reasoning off", f"set model {GPT_OSS_ARTIFACT}")
    assert (
        f"variation: {NATIVE}+reasoning=off+model={GPT_OSS_ARTIFACT} × "
        + GPT_OSS_ARTIFACT
    ) in written
    assert bench.skeleton(tried(repl)).body["reasoning_effort"] == "low"
    assert repl.at is not None and repl.at.name == GPT_OSS

    _ = say(f"set model {QWEN_ARTIFACT}")
    assert repl.prompt == f"alice {NATIVE}+reasoning=off #7> "
    assert repl.at is not None and repl.at.name == QWEN


def test_a_model_that_refuses_a_pick_is_refused_until_the_pick_is_set_otherwise(
    repl: Repl, say: Say
):
    _ = say(f"use {NATIVE}", "set reasoning on")

    written = say(f"set model {MISTRAL_ARTIFACT}")
    assert f"{MISTRAL_MODEL}: " in written and "doesn't reason" in written
    assert repl.failed
    assert repl.prompt == f"alice {NATIVE}+reasoning=on #7> "

    written = say("set reasoning off", f"set model {MISTRAL_ARTIFACT}")
    assert f"variation: {NATIVE}+reasoning=off+model={MISTRAL_ARTIFACT}" in written
    assert repl.at is not None and repl.at.name == MISTRAL


def test_a_hand_written_configuration_runs_under_the_handle_named(
    repl: Repl, bench: Bench, say: Say
):
    by_hand(bench)
    written = say("use by hand")
    assert "variation: by hand × ?" in written
    assert "by hand names no model: name the one to run it under" in written
    assert not repl.failed

    written = say(f"under {QWEN_ARTIFACT}")
    assert f"variation: by hand × {QWEN_ARTIFACT}" in written
    assert repl.prompt == f"alice by hand×{QWEN_ARTIFACT} #7> "
    assert repl.at is not None and repl.at.name == QWEN

    _ = say(f"use {LINES}")
    assert repl.under is None
    assert repl.prompt == f"alice {LINES} #7> "


def test_under_says_what_it_can_t_run_under(bench: Bench, say: Say):
    by_hand(bench)
    written = say(f"under {QWEN_ARTIFACT}", f"use {LINES}", f"under {GPT_OSS_ARTIFACT}")
    written += say("use by hand", "under nope")

    assert "the repl holds no configuration to run under it" in written
    assert (
        f"{LINES} runs under its model's handle: set model {GPT_OSS_ARTIFACT} instead"
        in written
    )
    assert "no model 'nope' for alice" in written


def test_set_puts_another_chunk_in_the_configuration(
    repl: Repl, bench: Bench, say: Say
):
    written = say(f"use {LINES}", "set reasoning off")

    assert repl.prompt == f"alice {LINES}+reasoning=off #7> "
    assert f"variation: {LINES}+reasoning=off × {QWEN_ARTIFACT}" in written
    body = bench.skeleton(tried(repl)).body
    assert body["chat_template_kwargs"] == {"enable_thinking": False}


def test_setting_the_configuration_s_own_chunk_unsets_it(repl: Repl, say: Say):
    _ = say(f"use {LINES}", "set sampling greedy")
    assert repl.prompt == f"alice {LINES}+sampling=greedy #7> "

    _ = say("set sampling recommended")
    assert repl.prompt == f"alice {LINES} #7> "


@pytest.mark.slow
def test_none_takes_an_optional_part_out(repl: Repl, bench: Bench, say: Say):
    written = say(f"use {NATIVE_TOOLS}", "set toolset none", "show")

    assert repl.prompt == f"alice {NATIVE_TOOLS}+toolset=none #7> "
    assert f"none (set; {NATIVE_TOOLS} has lookup)" in written
    assert "tools" not in bench.skeleton(tried(repl)).body

    _ = say("set toolset lookup")
    assert repl.prompt == f"alice {NATIVE_TOOLS} #7> "


def test_none_of_a_part_it_has_none_of_is_nothing_set(repl: Repl, say: Say):
    _ = say(f"use {LINES}", "set toolset none")

    assert repl.prompt == f"alice {LINES} #7> "


def test_use_puts_a_configuration_in_as_it_is(repl: Repl, say: Say):
    _ = say(f"use {LINES}", "set reasoning off", "use lines")

    assert repl.prompt == f"alice {LINES} #7> "


def test_set_says_what_it_can_t_set(say: Say):
    written = say("set reasoning off", f"use {LINES}", "set colour red")
    written += say("set reasoning nope", "set prompt none", "set model none")
    written += say("set model nope")

    assert "the repl holds no configuration to set it in" in written
    assert (
        "no part 'colour': instructions, few_shot, prompt, output, sampling, "
        + "reasoning, passthrough, translations, toolset, model"
    ) in written
    assert "no reasoning 'nope' for alice" in written
    assert "a configuration always has a prompt: only instructions" in written
    assert "a configuration always has a model" in written
    assert "no model 'nope' for alice" in written


@pytest.mark.slow
def test_save_keeps_the_variation_as_a_configuration_of_one_s_own(
    repl: Repl, bench: Bench, conn: Connection, say: Say
):
    _ = say(f"use {LINES}")
    origin = tried(repl).configuration
    written = say("set reasoning off", "save quiet")

    assert "saved as quiet: created" in written
    assert repl.prompt == "alice quiet #7> "

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
    assert f"variation: quiet × {QWEN_ARTIFACT}" in say("use quiet")
    assert f"variation: quiet × {QWEN_ARTIFACT}" in say("use alice/quiet")


@pytest.mark.slow
def test_saving_again_is_a_new_version_or_nothing(
    bench: Bench, conn: Connection, say: Say
):
    written = say(
        f"use {LINES}",
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
    assert "the repl holds no configuration to save" in say("save nothing")


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
    written = say("use bob/bobs-native", "save my-native")

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


def test_the_recommended_sampling_follows_the_model_set(say: Say):
    written = say(f"use {NATIVE}", f"set model {GPT_OSS_ARTIFACT}")

    assert "facts.sampling_unmatched" not in written
