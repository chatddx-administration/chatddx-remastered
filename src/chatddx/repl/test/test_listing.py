import pytest

from chatddx.inventory import Inventory
from chatddx.repl.test.sample import FREE_TEXT, GPT_OSS, QWEN, Say, line_of

pytestmark = pytest.mark.wip


def test_endpoints_are_listed_with_their_engines_and_clearance(
    world: Inventory, say: Say
):
    written = say("endpoints")

    assert line_of(written, QWEN).split() == [
        QWEN,
        QWEN,
        "Qwen/Qwen3-8B-AWQ",
        str(world.endpoints[QWEN].url),
        "sample",
        "typed",
    ]
    assert line_of(written, GPT_OSS).split()[2] == "openai/gpt-oss-20b"


def test_configurations_are_listed_with_their_parts_and_whose_they_are(say: Say):
    written = say("configurations")
    header = written.splitlines()[0].split()
    rows = [
        line.split()
        for line in written.splitlines()
        if line.strip().startswith(FREE_TEXT)
    ]

    assert header == [
        "configuration",
        "instructions",
        "few_shot",
        "prompt",
        "output",
        "sampling",
        "passthrough",
        "translations",
        "toolset",
        "owner",
    ]
    row = [
        *FREE_TEXT.split(),
        "—",
        "—",
        "case",
        "free-text",
        "(en)",
        "recommended",
        "(Qwen/Qwen3-8B-AWQ)",
        "—",
        "—",
        "—",
    ]
    assert rows == [row, [*row, "archive"]]
    assert "web (en)" in line_of(written, "plan-web (en, Qwen")
    guided = line_of(written, "free-text-guided (sv, Qwen")
    assert "clinician (sv)" in guided and "sample (sv)" in guided


def test_cases_are_listed_by_name_with_their_tags(say: Say):
    written = say("cases")

    assert "DutchFall10w  Dutchfall11w" in written
    assert "99 cases; tagged dutch-fall 30, edn 20, openxddx 49" in written
