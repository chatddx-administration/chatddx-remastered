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

pytestmark = pytest.mark.wip


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


def test_configurations_are_listed_with_their_parts_and_whose_they_are(bench: Bench):
    # Wide enough that no configuration's name wraps.
    repl = Repl(bench, console(record=True, width=400), seed=7)
    assert handle(repl, "configurations")
    written = repl.console.export_text()
    header = written.splitlines()[0].split()
    rows = [
        line.split() for line in written.splitlines() if line.strip().startswith(LINES)
    ]

    assert header == [
        "configuration",
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
    row = [
        *LINES.split(),
        "—",
        "—",
        "case",
        "lines",
        "(en)",
        "recommended",
        f"({QWEN_MODEL})",
        "—",
        "—",
        "—",
        "—",
    ]
    assert rows == [row, [*row, "archive"]]
    assert "lookup (en)" in line_of(written, NATIVE_TOOLS)
    assert f"on-budget ({QWEN_MODEL})" in line_of(
        written, f"budgeted (en, {QWEN_MODEL})"
    )
    guided = line_of(written, "lines-guided (sv)")
    assert "clinician (sv)" in guided and "guided (sv)" in guided


def test_cases_are_listed_by_name_with_their_tags(say: Say):
    written = say("cases")
    tags = Counter(tag for case in CASES.values() for tag in case.tags)
    counted = ", ".join(f"{tag} {n}" for tag, n in sorted(tags.items()))

    assert "  ".join(sorted(CASES)) in written
    assert f"{len(CASES)} cases; tagged {counted}" in written
