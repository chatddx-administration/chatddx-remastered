from pathlib import Path

import pytest

from chatddx.bench import Bench
from chatddx.cli import main
from chatddx.ledger import RunStarted
from chatddx.scripted import RUNS, load, ran_before, scripted_runs
from chatddx.scripted.test.helpers import UNFINISHED, went
from chatddx.test.world import QWEN_MODEL as MODEL, TEST, freed

HELD = {s.name: s for s in scripted_runs(TEST / RUNS)}


# The ran template ran each scripted run.
def held(bench: Bench, name: str) -> RunStarted:
    started = ran_before(bench, HELD[name])
    assert started is not None
    return started


@pytest.mark.parametrize("template", ["ran"], indirect=True)
@pytest.mark.parametrize(
    ("name", "outcomes"),
    [
        ("valid", {"matched": ("valid", None)}),
        ("stopped", {"crlf": ("stopped", None)}),
        ("unfinished", {"bom": ("completed", None)}),
        (
            "several",
            {
                "crlf": ("errored", "HTTP 503: loading"),
                "svenska": ("completed", UNFINISHED),
            },
        ),
        ("judged", {"noted": ("completed", None)}),
        ("appendix", {"whitespace with labs": ("completed", None)}),
    ],
)
@pytest.mark.slow
def test_each_scripted_run_runs_as_its_script_answers(
    bench: Bench, name: str, outcomes: dict[str, tuple[str, str | None]]
) -> None:
    scripted, started = HELD[name], held(bench, name)

    assert went(bench, started) == outcomes
    finished = bench.store.run(started.run).finished is not None
    assert finished == (not scripted.unfinished)
    assert bool(bench.scores_of(started.run)) == (finished and scripted.scored)


@pytest.mark.parametrize("template", ["ran"], indirect=True)
@pytest.mark.slow
def test_a_scripted_run_s_judges_are_served_as_plain_fakes(bench: Bench) -> None:
    started = held(bench, "judged")

    [judged] = [g for g in bench.scores_of(started.run) if g.name == "judged"]
    assert judged.score is not None
    called = [c.call for i in judged.score.items for c in i.judge_calls]
    assert called and all(c.error is None for c in called)


def test_a_scripted_run_is_its_file_s_name_and_says_what_it_can_t_read(
    tmp_path: Path,
) -> None:
    assert sorted(HELD) == sorted(p.stem for p in (TEST / RUNS).glob("*.toml"))
    path = tmp_path / "odd.toml"
    _ = path.write_text('description = "x"\nconfiguration = "lines"\n')
    with pytest.raises(ValueError, match="odd.toml"):
        _ = load(path)
    _ = path.write_text(
        'description = "x"\nconfiguration = "lines"\nendpoint = "e"\n'
        + 'cases = ["c"]\n[[turn]]\nwords = 1\n'
    )
    with pytest.raises(ValueError, match=r"turn 1 has no \['words'\]"):
        _ = load(path)


@pytest.mark.slow
def test_the_scripted_runs_command_runs_each_once(
    db: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    world = str(freed(tmp_path))

    main(["scripted-runs", "alice", "--world", world, "valid", "unfinished"])
    first = capsys.readouterr().out.splitlines()
    main(["scripted-runs", "alice", "--world", world, "valid"])
    second = capsys.readouterr().out.splitlines()

    assert [line.split(" × ")[0] for line in first] == [
        f"[scripted run unfinished] lines (en, {MODEL})",
        f"[scripted run valid] native (en, {MODEL})",
    ]
    assert first[0].split(": ", 1)[1].startswith("1 completed, unfinished, scored by 0")
    assert first[1].split(": ", 1)[1].startswith("1 valid, scored by")
    assert [line.split(", ran")[0] for line in second] == [first[1].split(", ran")[0]]
    assert first[1].split(" as run ")[1] == second[0].split(" as run ")[1]
    assert ", ran before as run " in second[0]
    with pytest.raises(SystemExit, match="no scripted run nope"):
        main(["scripted-runs", "alice", "--world", world, "nope"])
