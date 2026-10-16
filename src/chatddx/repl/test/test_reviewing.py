import shutil
from pathlib import Path

import pytest

from chatddx.bench import Bench
from chatddx.inventory import DirectorySource, Inventory
from chatddx.repl.test.helpers import Say, cells, tagged
from chatddx.scripted import RUNS, run, scripted_runs
from chatddx.test.world import LINES, NATIVE, QWEN, TEST

SCRIPTED = {s.name: s for s in scripted_runs(TEST / RUNS)}


def rows(written: str) -> list[str]:
    return [line for line in written.splitlines() if " × " in line]


def test_runs_says_when_there_are_none(say: Say):
    assert "alice has no runs" in say("runs")
    assert "a count is a whole number, not x" in say("runs x")
    assert "alice has no runs" in say("replay")


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
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


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_replay_shows_a_run_again_as_it_streamed(say: Say):
    live = say(f"cell {LINES} {QWEN}", "run noted").splitlines()
    replayed = say("replay").splitlines()

    start = next(i for i, line in enumerate(live) if line.startswith("trial:"))
    end = next(i for i, line in enumerate(live) if line.startswith("recorded as"))

    assert replayed[0].startswith("run ")
    assert replayed[0].endswith(f": {LINES} × {QWEN} × noted (seed 7)")
    assert ", finished, at http://127.0.0.1:" in replayed[1]
    assert "is the one that was sent" in replayed[2]
    streamed = [
        line for line in live[start + 1 : end] if not line.startswith("judging")
    ]
    assert replayed[3:] == streamed
    assert "[thinking] I am the fake vLLM" in replayed[3]


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_replay_shows_a_run_of_several_cases_again_by_its_lines(say: Say):
    _ = say(f"cell {NATIVE} {QWEN}", "run tag targets")
    targets = tagged("targets")

    replayed = say("replay")

    assert f"× {QWEN} × {len(targets)} cases (seed 7)" in replayed
    assert sorted(c[0] for c in cells(replayed) if c[2:] == ["valid"]) == targets
    assert any(c[:2] == ["answer", "answer"] for c in cells(replayed))


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_replay_takes_a_run_by_the_start_of_its_id(bench: Bench, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted", "run crlf")
    first = bench.runs()[-1]

    assert "× noted (seed 7)" in say(f"replay {str(first.run)[:8]}")
    assert "no run of yours starts with 'zzzz'" in say("replay zzzz")


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
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
    variation = bench.configuration(LINES)
    running = bench.start(variation, QWEN, [bench.family("noted").case], (7,)).first
    running.send()

    [row] = rows(say("runs"))
    assert "completed, unfinished" in row

    run = str(running.run)[:8]
    assert "unfinished: nothing to score" in say(f"score {run}")
    assert "nothing to score" in say("score")


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_show_sums_up_the_runs_with_what_it_shows(say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted", "run noted 8")

    written = say("show case noted")

    assert "2 runs of yours with it" in written
    assert ["differential", "2", "0", "0"] in cells(written)

    written = say("show scorer whole")

    assert "2 runs of yours it scored" in written
    assert "lines" not in written
    assert "no runs of yours it scored" in say("show scorer answer")


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_show_case_sums_up_only_its_own_items(say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted", "run tag targets")

    written = say("show case noted")

    assert "2 runs of yours with it" in written
    assert ["differential", "2", "0", "0"] in cells(written)


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_show_finds_the_runs_through_what_compiled_or_scored_them(say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted")

    assert "1 run of yours with it" in say("show output")
    assert "1 run of yours with it" in say("show prompt case")
    assert "1 run of yours it judged" in say("show judge verdict")
    assert "1 run of yours with it" in say("show expectation_schema targets")


@pytest.mark.slow
def test_replay_says_a_run_was_stopped(bench: Bench, say: Say):
    _ = run(bench, SCRIPTED["stopped"])

    written = say("replay")

    assert ["stopped"] in cells(written)
    assert "unread" not in written


@pytest.mark.slow
def test_show_judge_sums_up_only_what_it_judged(bench: Bench, say: Say):
    _ = run(bench, SCRIPTED["judged"])
    _ = run(bench, SCRIPTED["valid"])

    written = say("show judge verdict")

    assert "1 run of yours it judged, in 2 calls" in written
    assert ["judged", "note-comment", "1", "1", "0"] in cells(written)
    assert ["note-answer", "1", "1", "0"] in cells(written)
    assert "note-graded" not in written and "differential" not in written

    written = say("show judge graded")

    assert "1 run of yours it judged, in 3 calls" in written
    assert ["judged", "note-graded", "1", "0.5", "0"] in cells(written)

    written = say(f"show endpoint {QWEN}")

    assert "2 runs of yours at it" in written
    assert "judged 1 run of yours at it, in 5 calls" in written
    assert "no runs of yours it judged" in say("show judge remote")


@pytest.mark.slow
def test_score_counts_an_answer_that_never_came_apart(bench: Bench, say: Say):
    _ = run(bench, SCRIPTED["several"])

    written = say("score").splitlines()

    header = next(line for line in written if "no answer" in line)
    row = next(line for line in written if line.split()[:2] == ["lines", "text"])
    at = header.index("no answer")
    assert row[at : at + len("no answer")].strip() == "1"
    assert row.split()[2] == "0"


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_of_several_cases_is_replayed_and_tabled_by_case(say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run tag targets")

    written = say("replay").splitlines()

    at = written.index(next(line for line in written if line.startswith("case ")))
    targets = tagged("targets")
    assert [line.split()[0] for line in written[at + 1 : at + 1 + len(targets)]] == (
        targets
    )
    table = next(
        i for i, line in enumerate(written) if i > at and line.split()[:1] == ["case"]
    )
    tabled = written[table + 1 : table + 1 + len(targets)]
    assert [line.split()[0] for line in tabled] == targets
