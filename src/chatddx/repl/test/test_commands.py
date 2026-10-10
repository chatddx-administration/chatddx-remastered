import pytest

from chatddx.repl.commands import COMMANDS, complete, handle
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import PLAN, QWEN, Say, tried

pytestmark = pytest.mark.wip


def test_the_prompt_shows_the_cell(repl: Repl, say: Say):
    assert repl.prompt == "alice #7> "

    _ = say(f"use {PLAN}")
    assert repl.prompt == f"alice {PLAN} #7> "

    _ = say(f"on {QWEN}")
    assert repl.prompt == f"alice {PLAN}×{QWEN} #7> "


def test_help_lists_every_command_with_the_words_it_takes(say: Say):
    written = say("help")

    for verb in COMMANDS:
        assert verb in written

    assert "set PART CHUNK" in written
    assert "cell CONFIGURATION ENDPOINT" in written
    assert "show [KIND] [NAME...]" in written


def test_what_it_doesn_t_know_is_said_and_nothing_changes(repl: Repl, say: Say):
    written = say("use nope", "cell free-text nope", "on", "frobnicate", "use 'x")

    assert "no configuration 'nope' for alice" in written
    assert "no endpoint 'nope' in the inventory" in written
    assert "usage: on ENDPOINT" in written
    assert "no command 'frobnicate': try help" in written
    assert "No closing quotation" in written
    assert repl.cell.variation is None


def test_a_name_with_spaces_needs_no_quotes(repl: Repl, say: Say):
    _ = say(f"cell {PLAN} {QWEN}")
    assert repl.prompt == f"alice {PLAN}×{QWEN} #7> "

    _ = say(f"use '{PLAN}'")
    assert tried(repl).name == PLAN


def test_quit_leaves(repl: Repl):
    assert handle(repl, "quit") is False
    assert handle(repl, "exit") is False


def test_it_completes_a_command_and_then_its_names_word_by_word():
    names = {
        "configuration": ["free-text", PLAN, "plan", "plan (en, openai/gpt-oss-20b)"],
        "endpoint": [QWEN, "gpt-oss-20b@fake"],
        "part": ["prompt", "reasoning", "sampling"],
        "reasoning": ["off", "off (Qwen/Qwen3-8B-AWQ)", "on", "none"],
        "case": ["case-1", "case-2"],
        "kind": ["tag", "case", "configuration", "tool", "toolset"],
    }

    assert complete(names, "us") == ["use"]
    assert complete(names, "use pl") == ["plan"]
    assert complete(names, "use plan ") == ["(en,"]
    assert complete(names, "use plan (en, ") == [
        "Qwen/Qwen3-8B-AWQ)",
        "openai/gpt-oss-20b)",
    ]
    assert complete(names, "use plan (en, o") == ["openai/gpt-oss-20b)"]
    assert complete(names, f"cell {PLAN} q") == [QWEN]
    assert complete(names, "cell plan ") == ["(en,", QWEN, "gpt-oss-20b@fake"]
    assert complete(names, "on g") == ["gpt-oss-20b@fake"]
    assert complete(names, "set r") == ["reasoning"]
    assert complete(names, "set reasoning o") == ["off", "on"]
    assert complete(names, "set reasoning off ") == ["(Qwen/Qwen3-8B-AWQ)"]
    assert complete(names, "set reasoning n") == ["none"]
    assert complete(names, "show c") == ["case", "configuration"]
    assert complete(names, "show case case-") == ["case-1", "case-2"]
    assert complete(names, "frobnicate x") == []


def test_tags_complete_after_show_tag_each_once():
    names = {"kind": ["tag", "tool", "toolset"], "tag": ["dutch-fall", "edn"]}

    assert complete(names, "show t") == ["tag", "tool", "toolset"]
    assert complete(names, "show tag ") == ["dutch-fall", "edn"]
    assert complete(names, "show tag edn ") == ["dutch-fall"]


def test_the_names_complete_as_the_person_sees_them(repl: Repl):
    names = repl.completions()

    assert names["tag"] == ["dutch-fall", "edn", "openxddx"]
    assert {PLAN, "plan"} <= set(names["configuration"])
    assert {"off", "off (Qwen/Qwen3-8B-AWQ)", "none"} <= set(names["reasoning"])
    assert "none" not in names["sampling"]
    assert names["endpoint"] == ["gpt-oss-20b@fake", QWEN]
    assert len(names["case"]) == 99
