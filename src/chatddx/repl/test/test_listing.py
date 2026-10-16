from collections import Counter

import pytest

from chatddx.bench import Bench
from chatddx.inventory import Inventory
from chatddx.repl.commands import handle
from chatddx.repl.shell import Repl, console
from chatddx.repl.test.helpers import Say, line_of
from chatddx.test.world import (
    CASES,
    GPT_OSS,
    GPT_OSS_MODEL,
    LINES,
    NATIVE_TOOLS,
    QWEN,
    QWEN_BARE,
    QWEN_MODEL,
)


def test_endpoints_are_listed_with_their_engines_and_clearance(
    world: Inventory, say: Say
):
    written = say("endpoints")

    assert line_of(written, QWEN).split() == [
        QWEN,
        QWEN,
        QWEN_MODEL,
        str(world.endpoints[QWEN].url),
        "test",
        "typed",
    ]
    assert line_of(written, GPT_OSS).split()[2] == GPT_OSS_MODEL
    assert line_of(written, QWEN_BARE).split()[-1] == "test"


# Wide enough that no configuration's name wraps.
def listed(bench: Bench, line: str) -> str:
    repl = Repl(bench, console(record=True, width=400), seed=7)
    assert handle(repl, line)
    return repl.console.export_text()


@pytest.mark.slow
def test_configurations_are_listed_a_row_per_name_with_its_languages_and_parts(
    bench: Bench,
):
    written = listed(bench, "configurations")
    lines = written.splitlines()

    assert lines[0].split() == [
        "configuration",
        "languages",
        "instructions",
        "few_shot",
        "prompt",
        "output",
        "sampling",
        "reasoning",
        "passthrough",
        "translations",
        "toolset",
        "engine",
        "owner",
    ]
    assert line_of(written, f"{LINES} ").split() == [
        *("lines", "en", "—", "—", "case", "lines", "recommended", "—"),
        *("—", "—", "—", QWEN, "yours,", "from", "archive"),
    ]
    assert not [line for line in lines if line.rstrip().endswith("  archive")]
    assert "on-budget" in line_of(written, "budgeted")
    assert "high" in line_of(written, "reasoned")
    assert line_of(written, "lines-guided").split()[1:4] == ["en,", "sv", "clinician"]


@pytest.mark.slow
def test_judge_configurations_are_listed_apart(bench: Bench):
    lines = listed(bench, "configurations").splitlines()

    [apart] = [i for i, line in enumerate(lines) if line == "judge configurations"]
    names = [line.split("  ")[0].strip() for line in lines]
    assert "lines" in names[:apart]
    assert "judge" in names[apart:] and "judge" not in names[:apart]
    assert lines[apart + 1].split()[0] == "configuration"


@pytest.mark.slow
def test_configurations_name_lists_each_one_by_that_name(bench: Bench):
    written = listed(bench, "configurations lines")
    rows = [
        line.split() for line in written.splitlines() if line.strip().startswith(LINES)
    ]

    row = [LINES, "en", "case", "lines", "recommended", QWEN]
    assert rows == [row, [*row, "archive"]]
    assert "lookup" in line_of(
        listed(bench, f"configurations {NATIVE_TOOLS}"), NATIVE_TOOLS
    )
    assert "no configuration 'nope' for alice" in listed(bench, "configurations nope")


def test_cases_are_listed_by_name_with_their_tags(say: Say):
    written = say("cases")
    tags = Counter(tag for case in CASES.values() for tag in case.tags)
    counted = ", ".join(f"{tag} {n}" for tag, n in sorted(tags.items()))

    assert "  ".join(sorted(CASES)) in written
    assert f"{len(CASES)} cases; tagged {counted}" in written
