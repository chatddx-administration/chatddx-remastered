import pytest

from chatddx.repl.commands import COMMANDS, complete, handle
from chatddx.repl.running import case_and_seed
from chatddx.repl.shell import Repl
from chatddx.repl.test.helpers import Say, tried
from chatddx.test.world import (
    CASES,
    GPT_OSS,
    GPT_OSS_MODEL,
    MISTRAL,
    NATIVE,
    QWEN,
    QWEN_BARE,
    QWEN_MODEL,
    REMOTE,
)


def test_the_prompt_shows_the_cell(repl: Repl, say: Say):
    assert repl.prompt == "alice #7> "

    _ = say(f"use {NATIVE}")
    assert repl.prompt == f"alice {NATIVE} #7> "

    _ = say(f"on {QWEN}")
    assert repl.prompt == f"alice {NATIVE}×{QWEN} #7> "


def test_help_lists_every_command_with_the_words_it_takes(say: Say):
    written = say("help")

    for verb in COMMANDS:
        assert verb in written

    assert "set PART CHUNK" in written
    assert "cell CONFIGURATION ENDPOINT" in written
    assert "show [KIND] [NAME...]" in written
    assert "take [from OWNER] [TAG...]" in written
    assert "run tag TAG..." in written


def test_what_it_doesn_t_know_is_said_and_nothing_changes(repl: Repl, say: Say):
    written = say("use nope", "cell lines nope", "on", "frobnicate", "use 'x")

    assert "no configuration 'nope' for alice" in written
    assert "no endpoint 'nope' in the inventory" in written
    assert "usage: on ENDPOINT" in written
    assert "no command 'frobnicate': try help" in written
    assert "No closing quotation" in written
    assert repl.cell.variation is None


@pytest.mark.slow
def test_a_name_with_spaces_needs_no_quotes(repl: Repl, say: Say):
    _ = say(f"cell {NATIVE} {QWEN}")
    assert repl.prompt == f"alice {NATIVE}×{QWEN} #7> "

    _ = say(f"use '{NATIVE}'")
    assert tried(repl).name == NATIVE


def test_quit_leaves(repl: Repl):
    assert handle(repl, "quit") is False
    assert handle(repl, "exit") is False


def test_quit_takes_no_words(repl: Repl, say: Say):
    assert "usage: quit" in say("quit now")
    assert repl.failed


def test_it_completes_a_command_and_then_its_names_word_by_word():
    names = {
        "configuration": ["lines", NATIVE, "native", f"native (en, {GPT_OSS_MODEL})"],
        "endpoint": [QWEN, GPT_OSS],
        "part": ["prompt", "reasoning", "sampling"],
        "reasoning": ["off", f"off ({QWEN_MODEL})", "on"],
        "set:reasoning": ["off", f"off ({QWEN_MODEL})", "on", "none"],
        "case": ["case-1", "case-2"],
        "kind": ["tag", "case", "configuration", "tool", "toolset"],
    }

    assert complete(names, "us") == ["use"]
    assert complete(names, "use na") == ["native"]
    assert complete(names, "use native ") == ["(en,"]
    assert complete(names, "use native (en, ") == [
        f"{QWEN_MODEL})",
        f"{GPT_OSS_MODEL})",
    ]
    assert complete(names, "use native (en, o") == [f"{GPT_OSS_MODEL})"]
    assert complete(names, f"cell {NATIVE} q") == [QWEN]
    assert complete(names, "cell native ") == ["(en,", QWEN, GPT_OSS]
    assert complete(names, "on g") == [GPT_OSS]
    assert complete(names, "set r") == ["reasoning"]
    assert complete(names, "set reasoning o") == ["off", "on"]
    assert complete(names, "set reasoning off ") == [f"({QWEN_MODEL})"]
    assert complete(names, "set reasoning n") == ["none"]
    assert complete(names, "show c") == ["case", "configuration"]
    assert complete(names, "show case case-") == ["case-1", "case-2"]
    assert complete(names, "show reasoning n") == []
    assert complete(names, "frobnicate x") == []


def test_run_tag_completes_each_tag_once():
    names = {"case": ["targeted", "whitespace"], "tag": ["bytes", "swedish", "targets"]}

    assert complete(names, "run t") == ["tag", "targeted"]
    assert complete(names, "run tag ") == ["bytes", "swedish", "targets"]
    assert complete(names, "run tag targets ") == ["bytes", "swedish"]
    assert complete(names, "run tag targets s") == ["swedish"]
    assert complete(names, "ru") == ["run", "runs"]


def test_tags_complete_after_show_tag_each_once():
    names = {"kind": ["tag", "tool", "toolset"], "tag": ["bytes", "targets"]}

    assert complete(names, "show t") == ["tag", "tool", "toolset"]
    assert complete(names, "show tag ") == ["bytes", "targets"]
    assert complete(names, "show tag targets ") == ["bytes"]


def test_take_completes_from_and_then_each_tag_once():
    names = {"tag": ["bytes", "targets"]}

    assert complete(names, "take ") == ["from", "bytes", "targets"]
    assert complete(names, "take f") == ["from"]
    assert complete(names, "take from ") == []
    assert complete(names, "take from bob ") == ["bytes", "targets"]
    assert complete(names, "take targets ") == ["bytes"]


@pytest.mark.slow
def test_the_names_complete_as_the_person_sees_them(repl: Repl):
    names = repl.completions()

    assert names["tag"] == sorted({tag for case in CASES.values() for tag in case.tags})
    assert "native" in names["configuration"] and NATIVE not in names["configuration"]
    assert {"lines-guided (en)", "lines-guided (sv)"} <= set(names["configuration"])
    assert (
        "off" in names["reasoning"] and f"off ({QWEN_MODEL})" not in names["reasoning"]
    )
    assert "none" not in names["reasoning"]
    assert "none" in names["set:reasoning"]
    assert "set:sampling" not in names
    assert names["endpoint"] == [GPT_OSS, MISTRAL, QWEN_BARE, QWEN, REMOTE]
    assert names["case"] == [*sorted(CASES), "whitespace with labs"]


def test_run_completes_a_case_s_title_word_by_word_and_takes_a_seed_after_it():
    names = {"case": ["whitespace", "whitespace with labs"]}

    assert complete(names, "run wh") == ["whitespace"]
    assert complete(names, "run whitespace ") == ["with"]
    assert complete(names, "run whitespace with ") == ["labs"]
    assert case_and_seed(["whitespace", "with", "labs", "8"]) == [
        "whitespace with labs",
        "8",
    ]
    assert case_and_seed(["whitespace", "with", "labs"]) == ["whitespace with labs"]
    assert case_and_seed(["noted", "x"]) == ["noted", "x"]
