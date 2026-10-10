import re
import signal

import pytest

from chatddx.bench import Bench
from chatddx.factors.base import Finding, resolve
from chatddx.factors.trial import Trial
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.inventory import Inventory, start_up
from chatddx.ledger import Run
from chatddx.repl.render import Tally, Transcript
from chatddx.repl.shell import SEEDS, Repl
from chatddx.repl.test.sample import FREE_TEXT, GPT_OSS, PLAN, QWEN, Say
from chatddx.runner.run import Event, Running, Streamed
from chatddx.store import Store

pytestmark = pytest.mark.wip


def test_seed_draws_a_short_seed_or_holds_one(repl: Repl, say: Say):
    written = say("seed")

    assert 0 <= repl.seed < SEEDS
    assert f"seed: #{repl.seed}" in written

    _ = say("seed 2147483647")
    assert repl.prompt == "alice #2147483647> "


def test_seed_says_what_isn_t_a_seed(repl: Repl, say: Say):
    written = say("seed -1", "seed 2147483648", "seed none")

    assert written.count("a seed is a whole number from 0 to 2147483647") == 3
    assert repl.seed == 7


def test_seed_says_a_greedy_configuration_isn_t_sent_it(say: Say):
    assert "greedy" not in say(f"cell {FREE_TEXT} {QWEN}", "seed 1")
    assert "greedy: the seed isn't sent" in say("set sampling greedy", "seed 2")


def line_of(written: str, start: str) -> str:
    [line] = [line for line in written.splitlines() if line.startswith(start)]
    return line


def ran(bench: Bench) -> list[Run]:
    return [Store(bench.conn).run(r.run) for r in bench.runs()]


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_run_streams_a_run_of_the_cell_and_scores_it(bench: Bench, say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")

    assert f"trial: {FREE_TEXT} × {QWEN} × Dutchfall11w (seed 7)" in written
    assert "[thinking] I am the fake vLLM" in written
    assert re.search(
        r"Fake diagnosis \w\nFake diagnosis \w\nFake diagnosis \w", written
    )
    assert re.search(r"\(\d+ in, \d+ out\)", written)
    assert re.search(r"differential\n  1\. Fake diagnosis \w\n  2\.", written)
    assert "valid" not in written
    assert "scores" in written
    assert "not listed" in line_of(written, "              differential")
    assert "recorded as run 1 of trial" in written

    [run] = ran(bench)
    assert run.finished is not None
    assert run.started.endpoint is not None and run.started.endpoint.name == QWEN
    assert [s.score for s in Store(bench.conn).scores_of(run.started.run)]


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_each_run_is_recorded_as_a_run_of_its_trial(bench: Bench, say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w", "run Dutchfall11w")

    first, again = re.findall(r"recorded as run (\d+) of trial (\w{6})", written)

    assert (first[0], again[0]) == ("1", "2")
    assert first[1] == again[1]
    assert len({r.started.trial for r in ran(bench)}) == 1


def test_run_needs_a_whole_cell(bench: Bench, say: Say):
    written = say(f"use {FREE_TEXT}", "run Dutchfall11w")

    assert "the cell needs a configuration and an endpoint" in written
    assert ran(bench) == []


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_run_takes_a_seed_of_its_own(repl: Repl, bench: Bench, say: Say):
    written = say(
        f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w 42", "run Dutchfall11w x"
    )

    assert "× Dutchfall11w (seed 42)" in written
    assert "a seed is a whole number from 0 to 2147483647, not x" in written
    assert repl.seed == 7

    [run] = ran(bench)
    assert resolve(bench.get, run.started.trial, Trial).seeds == (42,)


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_structured_answer_is_checked_and_its_views_read(say: Say):
    written = say(f"cell {PLAN} {QWEN}", "run casesfromedn1")

    assert "\nvalid\n" in written
    assert "differential\n  1. fake diagnosis 1\n  2. fake diagnosis 2" in written
    assert "warning\n  1. fake acute warning" in written
    assert 'differential (diagnoses)\n  1. {"diagnosis": "fake diagnosis 1"' in written
    assert "not named" in line_of(written, "              warning")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_tool_contract_shows_the_call_the_answer_is_given_through(say: Say):
    written = say(f"cell diagnoses-tool {QWEN}", "run casesfromedn1")

    assert '[final_result] {"diagnoses": ["fake diagnoses 1"' in written
    assert "\nvalid\n" in written


@pytest.mark.usefixtures("fake")
def test_run_is_refused_where_the_gate_refuses(bench: Bench, say: Say):
    written = say(f"cell plan-web {QWEN}", "run casesfromedn1")

    assert "refused: the skeleton's tools would get content from source sample" in (
        written
    )
    assert "trial:" not in written
    assert ran(bench) == []


def test_run_is_refused_an_endpoint_that_doesn_t_answer(bench: Bench, say: Say):
    written = say(f"cell plan {GPT_OSS}", "run casesfromedn1")

    assert f"refused: endpoint '{GPT_OSS}' can't be confirmed" in written
    assert ran(bench) == []


@pytest.mark.slow
def test_a_run_that_runs_away_is_cut_short_and_what_came_scored(
    world: Inventory, bench: Bench, say: Say
):
    startup = start_up(world, bench.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])], runaway=True):
        written = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")

    assert "stopped: nothing but whitespace for 100 tokens" in written
    assert re.search(r"differential\n  1\. Fake diagnosis \w", written)
    assert "recorded as run 1 of trial" in written

    [run] = ran(bench)
    [item] = run.items
    assert item.call.error == "stopped: nothing but whitespace for 100 tokens"


# A structure cut short isn't salvaged, so its answer can't be read.
@pytest.mark.slow
def test_a_structured_answer_cut_short_is_unread(
    world: Inventory, bench: Bench, say: Say
):
    startup = start_up(world, bench.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])], runaway=True):
        written = say(f"cell {PLAN} {QWEN}", "run casesfromedn1")

    assert "stopped: nothing but whitespace for 100 tokens" in written
    assert "unread: the content isn't JSON" in written
    assert "no answer" in written


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_a_greedy_cell_runs_without_its_seed(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "set sampling greedy", "run Dutchfall11w")

    assert "greedy: the seed isn't sent" in written
    assert "recorded as run 1 of trial" in written
    assert "seed=7" not in written


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_batch_runs_the_cell_on_each_case_tagged_a_line_to_each(bench: Bench, say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "batch edn")

    assert f"batch: {FREE_TEXT} × {QWEN} × 20 cases tagged edn, seed 7" in written
    assert line_of(written, "case    ").split() == ["case", "tokens", "outcome"]
    assert line_of(written, "casesfromedn1 ").split()[2] == "completed"
    assert "stopped after" not in written

    [run] = ran(bench)
    assert len(run.items) == 20
    summed = line_of(written, " free-text  text").split()
    assert summed == ["free-text", "text", "0", "—", "—", "20"]


def test_batch_says_what_it_can_t_run(say: Say):
    assert "the cell needs a configuration and an endpoint" in say("batch edn")
    assert "usage: batch TAG..." in say(f"cell {FREE_TEXT} {QWEN}", "batch")
    assert "no case tagged nowhere for alice" in say("batch nowhere")


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_batch_runs_the_cases_with_any_of_its_tags(bench: Bench, say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "batch edn nowhere dutch-fall")

    assert "50 cases tagged edn or nowhere or dutch-fall" in written
    [run] = ran(bench)
    assert len(run.items) == 50


def pressing(say: Say, *lines: str) -> str:
    try:
        return say(*lines)
    finally:
        assert signal.getsignal(signal.SIGINT) is signal.default_int_handler


# Presses Ctrl-C as the `at`th token of the first call streams, `presses` times.
def press_at(monkeypatch: pytest.MonkeyPatch, at: int, presses: int = 1) -> None:
    pressed = False
    count = Tally.count
    event = Transcript.event

    def press(tokens: int) -> None:
        nonlocal pressed
        if tokens >= at and not pressed:
            pressed = True
            for _ in range(presses):
                signal.raise_signal(signal.SIGINT)

    def counted(self: Tally, tokens: int) -> None:
        count(self, tokens)
        press(tokens)

    def evented(self: Transcript, e: Event) -> None:
        event(self, e)
        if isinstance(e, Streamed):
            press(e.delta.tokens)

    monkeypatch.setattr(Tally, "count", counted)
    monkeypatch.setattr(Transcript, "event", evented)


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_ctrl_c_stops_a_run_as_it_streams_and_it_is_recorded_as_stopped(
    bench: Bench, say: Say, monkeypatch: pytest.MonkeyPatch
):
    press_at(monkeypatch, 5)
    written = pressing(say, f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")

    assert "[thinking] I am the fake" in written
    assert "(stopped)" in written
    assert "recorded as run 1 of trial" in written

    [run] = ran(bench)
    [item] = run.items
    assert item.call.error == "stopped"
    assert run.finished is not None


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_ctrl_c_lets_the_case_under_way_finish_then_stops_the_batch(
    bench: Bench, say: Say, monkeypatch: pytest.MonkeyPatch
):
    press_at(monkeypatch, 5)
    written = pressing(say, f"cell {FREE_TEXT} {QWEN}", "batch edn")

    [run] = ran(bench)
    [item] = run.items
    assert item.call.error is None
    assert "stopped after 1 of 20 cases" in written
    assert "completed" in written
    assert run.finished is not None


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_ctrl_c_again_stops_the_case_under_way_too(
    bench: Bench, say: Say, monkeypatch: pytest.MonkeyPatch
):
    press_at(monkeypatch, 5, presses=2)
    written = pressing(say, f"cell {FREE_TEXT} {QWEN}", "batch edn")

    [run] = ran(bench)
    [item] = run.items
    assert item.call.error == "stopped"
    assert "stopped after 0 of 20 cases" not in written
    assert re.search(r"casesfromedn\d+ +\d+  stopped", written)
    assert "stopped after 1 of 20 cases" in written


@pytest.mark.slow
@pytest.mark.usefixtures("fake")
def test_ctrl_c_waits_for_a_run_to_be_written_down_and_scored(
    bench: Bench, say: Say, monkeypatch: pytest.MonkeyPatch
):
    finish = Running.finish

    def pressed(self: Running) -> list[Finding]:
        signal.raise_signal(signal.SIGINT)
        return finish(self)

    monkeypatch.setattr(Running, "finish", pressed)
    written = pressing(say, f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")

    assert "recorded as run 1 of trial" in written
    [run] = ran(bench)
    assert run.finished is not None
    assert Store(bench.conn).scores_of(run.started.run)
