import shutil
from pathlib import Path

import pytest

from chatddx.bench import Bench
from chatddx.conftest import WORLD
from chatddx.inventory import DirectorySource, Inventory
from chatddx.repl.test.sample import FREE_TEXT, PLAN, QWEN, Say


def rows(written: str) -> list[str]:
    return [line for line in written.splitlines() if " × " in line]


def test_runs_says_when_there_are_none(say: Say):
    assert "alice has no runs" in say("runs")
    assert "a count is a whole number, not x" in say("runs x")
    assert "alice has no runs" in say("replay")


@pytest.mark.usefixtures("fake")
def test_runs_lists_the_latest_first_with_how_each_went(say: Say):
    _ = say(
        f"cell {FREE_TEXT} {QWEN}",
        "run Dutchfall11w",
        f"use {PLAN}",
        "run casesfromedn1",
    )
    written = say("runs")
    latest, first = rows(written)

    assert f"{PLAN} × {QWEN} × casesfromedn1 (seed 7)" in latest
    assert " valid " in latest
    assert "plan 0/0/0/—" in written
    assert f"{FREE_TEXT} × {QWEN} × Dutchfall11w (seed 7)" in first
    assert " completed " in first

    [only] = rows(say("runs 1"))
    assert "casesfromedn1" in only


@pytest.mark.usefixtures("fake")
def test_replay_shows_a_run_again_as_it_streamed(say: Say):
    live = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w").splitlines()
    replayed = say("replay").splitlines()

    start = next(i for i, line in enumerate(live) if line.startswith("trial:"))
    end = next(i for i, line in enumerate(live) if line.startswith("recorded as"))

    assert replayed[0].startswith("run ")
    assert replayed[0].endswith(f": {FREE_TEXT} × {QWEN} × Dutchfall11w (seed 7)")
    assert ", finished, at http://127.0.0.1:" in replayed[1]
    assert "is the one that was sent" in replayed[2]
    assert replayed[3:] == live[start + 1 : end]
    assert "[thinking] I am the fake vLLM" in replayed[3]


@pytest.mark.usefixtures("fake")
def test_replay_shows_a_batch_again_by_its_lines(say: Say):
    _ = say(f"cell {PLAN} {QWEN}", "batch edn")

    replayed = say("replay")

    assert f"× {QWEN} × 20 cases (seed 7)" in replayed
    assert len([line for line in replayed.splitlines() if "  valid" in line]) == 20
    assert "plan          plan" in replayed


@pytest.mark.usefixtures("fake")
def test_replay_takes_a_run_by_the_start_of_its_id(bench: Bench, say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w", "run casesfromedn1")
    first = bench.runs()[-1]

    assert "× Dutchfall11w (seed 7)" in say(f"replay {str(first.run)[:8]}")
    assert "no run of yours starts with 'zzzz'" in say("replay zzzz")


@pytest.mark.usefixtures("fake")
def test_replay_says_when_the_request_would_render_otherwise_now(
    bench: Bench, world: Inventory, tmp_path: Path, say: Say
):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")
    moved = tmp_path / "vignettes"
    _ = shutil.copytree(WORLD.parent / "vignettes", moved)
    _ = (moved / "Dutchfall11w.txt").write_text("another vignette")
    source = DirectorySource(name="sample", path=moved)
    bench.inventory = world.model_copy(update={"sources": {"sample": source}})

    written = say("replay")

    assert (
        "Dutchfall11w: rendered again, the request differs: the vignette at the "
        + "source isn't the one sent"
    ) in written


@pytest.mark.usefixtures("fake")
def test_an_unfinished_run_is_listed_so_and_left_unscored(bench: Bench, say: Say):
    variation = bench.configuration(FREE_TEXT, bench.endpoint(QWEN))
    running = bench.start(variation, QWEN, [bench.family("Dutchfall11w").case], 7)
    running.send()

    [row] = rows(say("runs"))
    assert "completed, unfinished" in row

    run = str(running.run)[:8]
    assert "unfinished: nothing to score" in say(f"score {run}")
    assert "nothing to score" in say("score")


@pytest.mark.usefixtures("fake")
def test_show_sums_up_the_runs_with_what_it_shows(say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w", "run Dutchfall11w 8")

    written = say("show case Dutchfall11w")

    assert "2 runs of yours with it" in written
    assert ["differential", "2", "0", "0"] in [
        line.split() for line in written.splitlines()
    ]

    written = say("show scorer raw")

    assert "2 runs of yours it scored" in written
    assert "free-text" not in written
    assert "no runs of yours it scored" in say("show scorer plan")
