import io
from pathlib import Path

import pytest

from chatddx.cli import main
from chatddx.test.world import LINES, QWEN, TEST

pytestmark = pytest.mark.solidified


def test_the_shell_reads_lines_from_a_pipe_and_keeps_them(
    db: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setenv("DB_NAME", db)
    lines = [f"cell {LINES} {QWEN}", "seed 42", "set reasoning off", "quit"]
    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(lines) + "\n"))
    history = tmp_path / "history"

    main(["repl", "alice", "--world", str(TEST), "--history", str(history)])

    out = capsys.readouterr().out
    assert f"cell: {LINES} × {QWEN}" in out
    assert f"alice {LINES}×{QWEN} #42> set reasoning off" in out
    assert f"cell: {LINES}+reasoning=off × {QWEN}" in out
    assert history.exists()


def test_a_piped_session_stops_at_its_first_error(
    db: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setenv("DB_NAME", db)
    lines = ["seed 42", "use nope", "seed 43", "quit"]
    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(lines) + "\n"))

    with pytest.raises(SystemExit) as stopped:
        main(["repl", "alice", "--world", str(TEST), "--history", str(tmp_path / "h")])

    assert stopped.value.code == 1
    out = capsys.readouterr().out
    assert "no configuration 'nope' for alice" in out
    assert "seed 43" not in out


def test_the_shell_needs_a_person(db: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DB_NAME", db)

    with pytest.raises(SystemExit, match="no person 'nobody'"):
        main(["repl", "nobody", "--world", str(TEST)])
