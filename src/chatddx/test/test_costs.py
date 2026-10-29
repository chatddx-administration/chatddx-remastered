from pathlib import Path

import pytest

from chatddx.test.costs import Cost, command, logged, medians, quoted, read, write


def cost(command: str, seconds: float, status: int = 0, beside: int = 0) -> Cost:
    return Cost(
        "2026-10-29T00:00:00Z", "container", seconds, status, beside, "abc", command
    )


def test_a_command_is_as_typed_its_plugins_left_out() -> None:
    assert command(["-n", "4", "-p", "chatddx.test.budget"]) == "pytest -n 4"
    assert command(["-m", "not slow", "-pno:cacheprovider"]) == "pytest -m 'not slow'"
    assert command([]) == "pytest"


def test_a_command_is_as_typed_its_verbosity_left_out() -> None:
    assert command(["-qq", "-m", "browser", "--verbose", "-v"]) == "pytest -m browser"
    assert command(["-vk", "x"]) == "pytest -vk x"


def test_a_cost_reads_as_it_is_written() -> None:
    written = cost("pytest -m 'not\tslow'", 61.25).written()
    assert written.endswith("\tpytest -m 'not slow'\n")
    assert Cost.read(written.rstrip("\n")) == cost("pytest -m 'not slow'", 61.2)


def test_medians_weigh_recent_passes_run_alone_on_the_machine() -> None:
    costs = [cost("pytest", s) for s in (900, 1, 2, 3, 4, 5)]
    costs += [cost("pytest", 99, status=1), cost("pytest", 99, beside=2)]
    costs += [Cost("t", "devshell", 99, 0, 0, "abc", "pytest")]
    assert medians(costs, "container") == {"pytest": 3}


def test_a_figure_is_rewritten_only_once_far_enough_off() -> None:
    text = (
        "- `pytest` runs every test ~220s.\n"
        + "- `pytest -n 4` fast given absence of\n"
        + "  other loads, ~110s.\n"
        + "\n"
        + "- `ruff check` ~2s, besides `pytest` ~220s\n"
    )
    took = {"pytest": 150.0, "pytest -n 4": 40.0}
    assert quoted(text, took) == text.replace("~110s", "~40s")
    assert quoted(text, {"pytest": 120.0}) == text.replace("~220s.", "~120s.")


def test_a_figure_a_stamp_pending_holds_is_rewritten_as_written_now() -> None:
    text = (
        "<<<<<<< signed\n"
        + "- `pytest` ~220s\n"
        + "=======\n"
        + "- `pytest` takes ~220s\n"
        + ">>>>>>> @"
        + "stamp\n"
    )
    assert quoted(text, {"pytest": 61.25}) == text.replace("takes ~220s", "takes ~61s")


def test_write_folds_the_spool_and_rewrites_the_figures(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spool, log, doc = tmp_path / "spool", tmp_path / "log", tmp_path / "AGENTS.md"
    logged(cost("pytest", 61.25), spool, log)
    assert not spool.exists()
    log.touch()
    logged(cost("pytest", 61.25), spool, log)
    _ = doc.write_text("- `pytest` ~220s\n")
    write(spool, log, [doc])
    assert not spool.exists()
    assert read(log) == [cost("pytest", 61.2)]
    assert doc.read_text() == "- `pytest` ~61s\n"
    assert capsys.readouterr().out == "log: 1 folded\nAGENTS.md: figures rewritten\n"
    write(spool, log, [doc])
    assert capsys.readouterr().out == "nothing to write\n"
