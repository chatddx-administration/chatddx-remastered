import shutil
from pathlib import Path

import pytest

from chatddx.bench import Bench
from chatddx.inventory import DirectorySource, Inventory
from chatddx.repl.test.helpers import Say, cells, tagged
from chatddx.test.world import LINES, NATIVE, QWEN, TEST

pytestmark = pytest.mark.wip


def rows(written: str) -> list[str]:
    return [line for line in written.splitlines() if " × " in line]


def test_runs_says_when_there_are_none(say: Say):
    assert "alice has no runs" in say("runs")
    assert "a count is a whole number, not x" in say("runs x")
    assert "alice has no runs" in say("replay")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_runs_lists_the_latest_first_with_how_each_went(say: Say):
    _ = say(
        f"cell {LINES} {QWEN}",
        "run noted",
        f"use {NATIVE}",
        "run crlf",
    )
    written = say("runs")
    latest, first = rows(written)

    assert f"{NATIVE} × {QWEN} × crlf (seed 7)" in latest
    assert " valid " in latest
    assert "answer 0/0/0/—" in written
    assert f"{LINES} × {QWEN} × noted (seed 7)" in first
    assert " completed " in first

    [only] = rows(say("runs 1"))
    assert "crlf" in only


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_replay_shows_a_run_again_as_it_streamed(say: Say):
    live = say(f"cell {LINES} {QWEN}", "run noted").splitlines()
    replayed = say("replay").splitlines()

    start = next(i for i, line in enumerate(live) if line.startswith("trial:"))
    end = next(i for i, line in enumerate(live) if line.startswith("recorded as"))

    assert replayed[0].startswith("run ")
    assert replayed[0].endswith(f": {LINES} × {QWEN} × noted (seed 7)")
    assert ", finished, at http://127.0.0.1:" in replayed[1]
    assert "is the one that was sent" in replayed[2]
    assert replayed[3:] == live[start + 1 : end]
    assert "[thinking] I am the fake vLLM" in replayed[3]


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_replay_shows_a_batch_again_by_its_lines(say: Say):
    _ = say(f"cell {NATIVE} {QWEN}", "batch targets")
    targets = tagged("targets")

    replayed = say("replay")

    assert f"× {QWEN} × {len(targets)} cases (seed 7)" in replayed
    assert sorted(c[0] for c in cells(replayed) if c[2:] == ["valid"]) == targets
    assert any(c[:2] == ["answer", "answer"] for c in cells(replayed))


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_replay_takes_a_run_by_the_start_of_its_id(bench: Bench, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted", "run svenska")
    first = bench.runs()[-1]

    assert "× noted (seed 7)" in say(f"replay {str(first.run)[:8]}")
    assert "no run of yours starts with 'zzzz'" in say("replay zzzz")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_replay_says_when_the_request_would_render_otherwise_now(
    bench: Bench, world: Inventory, tmp_path: Path, say: Say
):
    _ = say(f"cell {LINES} {QWEN}", "run noted")
    moved = tmp_path / "vignettes"
    _ = shutil.copytree(TEST / "vignettes", moved)
    _ = (moved / "noted.txt").write_text("another vignette")
    source = DirectorySource(name="test", path=moved)
    sources = {**world.sources, "test": source}
    bench.inventory = world.model_copy(update={"sources": sources})

    written = say("replay")

    assert (
        "noted: rendered again, the request differs: the vignette at the "
        + "source isn't the one sent"
    ) in written


@pytest.mark.usefixtures("fake")
def test_an_unfinished_run_is_listed_so_and_left_unscored(bench: Bench, say: Say):
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
    running = bench.start(variation, QWEN, [bench.family("noted").case], 7)
    running.send()

    [row] = rows(say("runs"))
    assert "completed, unfinished" in row

    run = str(running.run)[:8]
    assert "unfinished: nothing to score" in say(f"score {run}")
    assert "nothing to score" in say("score")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_show_sums_up_the_runs_with_what_it_shows(say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted", "run noted 8")

    written = say("show case noted")

    assert "2 runs of yours with it" in written
    assert ["differential", "2", "0", "0"] in cells(written)

    written = say("show scorer whole")

    assert "2 runs of yours it scored" in written
    assert "lines" not in written
    assert "no runs of yours it scored" in say("show scorer answer")
