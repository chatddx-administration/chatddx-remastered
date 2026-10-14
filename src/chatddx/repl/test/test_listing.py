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
def test_configurations_are_listed_a_row_per_name_and_language_with_their_models(
    bench: Bench,
):
    written = listed(bench, "configurations")
    lines = written.splitlines()

    assert lines[0].split() == [
        "configuration",
        "models",
        "instructions",
        "few_shot",
        "prompt",
        "output",
        "sampling",
        "reasoning",
        "passthrough",
        "translations",
        "toolset",
        "owner",
    ]
    [at] = [i for i, line in enumerate(lines) if line.split()[:2] == ["lines", "(en)"]]
    assert lines[at].split() == [
        *("lines", "(en)", "gpt-oss-20b", "—", "—", "case", "lines", "(en)"),
        *("recommended", "—", "—", "—", "—", "yours,", "from", "archive"),
    ]
    assert [line.split() for line in lines[at + 1 : at + 3]] == [
        ["mistral-7b"],
        ["Qwen3-8B-AWQ"],
    ]
    assert not [line for line in lines if line.rstrip().endswith("  archive")]
    assert "Qwen3-8B-AWQ  " in line_of(written, "budgeted (en)")
    assert "on-budget" in line_of(written, "budgeted (en)")
    assert "varies" in line_of(written, "reasoned (en)")
    guided = line_of(written, "lines-guided (sv)")
    assert "every model" in guided and "guided (sv)" in guided


@pytest.mark.slow
def test_configurations_name_lists_its_variants_per_model(bench: Bench):
    written = listed(bench, "configurations lines")
    rows = [
        line.split() for line in written.splitlines() if line.strip().startswith(LINES)
    ]

    row = [*LINES.split(), "case", "lines", "(en)", "recommended", f"({QWEN_MODEL})"]
    assert rows == [row, [*row, "archive"]]
    assert len([line for line in written.splitlines() if "lines (en, " in line]) == 6
    assert "lookup (en)" in line_of(
        listed(bench, f"configurations {NATIVE_TOOLS}"), NATIVE_TOOLS
    )
    assert "no configuration 'nope' for alice" in listed(bench, "configurations nope")


def test_cases_are_listed_by_name_with_their_tags(say: Say):
    written = say("cases")
    tags = Counter(tag for case in CASES.values() for tag in case.tags)
    counted = ", ".join(f"{tag} {n}" for tag, n in sorted(tags.items()))

    assert "  ".join(sorted(CASES)) in written
    assert f"{len(CASES)} cases; tagged {counted}" in written
