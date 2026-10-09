import io
from pathlib import Path

import pytest

from chatddx.cli import main
from chatddx.repl.test.sample import FREE_TEXT, QWEN, WORLD


def test_the_shell_reads_lines_from_a_pipe_and_keeps_them(
    db: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setenv("DB_NAME", db)
    lines = [f"cell {FREE_TEXT} {QWEN}", "seed 42", "set reasoning off", "quit"]
    monkeypatch.setattr("sys.stdin", io.StringIO("\n".join(lines) + "\n"))
    history = tmp_path / "history"

    main(["repl", "alice", "--world", str(WORLD), "--history", str(history)])

    out = capsys.readouterr().out
    assert f"cell: {FREE_TEXT} × {QWEN}" in out
    assert f"alice {FREE_TEXT}×{QWEN} #42> set reasoning off" in out
    assert f"cell: {FREE_TEXT}+reasoning=off × {QWEN}" in out
    assert history.exists()


def test_the_shell_needs_a_person(db: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DB_NAME", db)

    with pytest.raises(SystemExit, match="no person 'nobody'"):
        main(["repl", "nobody", "--world", str(WORLD)])
