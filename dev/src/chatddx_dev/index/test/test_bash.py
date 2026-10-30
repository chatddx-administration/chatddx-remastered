from pathlib import Path

import pytest

from chatddx_dev import index, project
from chatddx_dev.index import bash
from chatddx_dev.index.facts import Comment, Entry, Facts, Named, dumped, loaded
from chatddx_dev.project import Class, Part, Stage

SCRIPT = """\
#!/usr/bin/env bash
# Usage: ./run.sh
set -euo pipefail

# Policy: the list.
WHAT=(a b)

go() {
  # Heads-up: inside.
  echo "$1" # Compromise: trailing.
}
"""

TESTS = """\
#!/usr/bin/env bats

# Accommodating for bats.
@test "it goes" {
  run go
}
"""


def test_a_script_s_facts_are_its_functions_assignments_and_comments_its_shebang_left_out(
    tmp_path: Path,
) -> None:
    script = tmp_path / "dev" / "run.sh"
    script.parent.mkdir()
    _ = script.write_text(SCRIPT)
    assert bash.facts(script, tmp_path) == Facts(
        "dev/run.sh",
        (Named("WHAT", 6, 6, 0), Named("go", 8, 11, 0)),
        (
            Comment(2, 0, "# Usage: ./run.sh", True),
            Comment(5, 0, "# Policy: the list.", True),
            Comment(9, 2, "# Heads-up: inside.", True),
            Comment(10, 12, "# Compromise: trailing.", False),
        ),
        (),
        (Entry("run.sh", "`run.sh`", ("`dev/run.sh`", "", "Usage: ./run.sh")),),
    )


def test_a_bats_test_is_named_by_its_description(tmp_path: Path) -> None:
    tests = tmp_path / "run.bats"
    _ = tests.write_text(TESTS)
    facts = bash.facts(tests, tmp_path)
    assert facts.names == (Named("it goes", 4, 6, 0),)
    assert facts.comments == (Comment(3, 0, "# Accommodating for bats.", True),)


def test_facts_read_as_they_are_dumped(tmp_path: Path) -> None:
    script = tmp_path / "run.sh"
    _ = script.write_text(SCRIPT)
    read = [bash.facts(script, tmp_path)]
    assert loaded(dumped(read)) == read


def test_a_part_s_scripts_are_indexed_under_its_name_once_its_comments_are_stamped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "dev").mkdir()
    _ = (tmp_path / "dev" / "run.sh").write_text(SCRIPT)
    _ = (tmp_path / "dev" / "notes.txt").write_text("# not a script\n")
    monkeypatch.setattr(project, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(index, "COMMENTS", tmp_path / "docs" / "comments")

    def parts(stage: Stage) -> dict[str, Part]:
        return {"dev": Part(stage, Class.MACHINERY, None, ("dev",))}

    monkeypatch.setattr(project, "PARTS", parts(Stage.NAMED))
    assert index.proofs() == []

    monkeypatch.setattr(project, "PARTS", parts(Stage.DRAFTED))
    [proof] = index.proofs()
    assert proof.path == tmp_path / "docs" / "comments" / "dev.md"
    assert proof.current is None
    assert "## `dev/run.sh:go`\n\n```\n# Heads-up: inside.\n```" in proof.written
    assert "## `dev/run.sh:WHAT`\n\n```\n# Policy: the list.\n```" in proof.written
    assert "not a script" not in proof.written


COMMAND = """\
#!/usr/bin/env bash
# shellcheck disable=SC2034
# Usage: ./tool.sh {go | stop}: goes or stops.
set -euo pipefail
MAIN=${MAIN:-main}
export OWN=1

go() {
  echo "$TOKEN $OWN $MAIN $HOME"
  for item in a; do echo "$item"; done
}

case "${1:-}" in
go | stop) "$1" ;;
*) exit 1 ;;
esac
"""

LIBRARY = """\
# shellcheck shell=bash
# Usage: . lib.sh, then said <word>: says it.
said() {
  echo "$1 $LOUD"
}

# Heads-up: apart from said.
quiet() {
  :
}
"""


def test_a_command_s_surface_is_its_usage_its_commands_and_its_environment(
    tmp_path: Path,
) -> None:
    command = tmp_path / "dev" / "tool.sh"
    command.parent.mkdir()
    _ = command.write_text(COMMAND)
    assert bash.facts(command, tmp_path).surface == (
        Entry(
            "tool.sh",
            "`tool.sh`",
            (
                "`dev/tool.sh`",
                "",
                "Usage: ./tool.sh {go | stop}: goes or stops.",
                "",
                "* `go`",
                "* `stop`",
                "* `$MAIN`",
                "* `$TOKEN`",
            ),
        ),
    )


def test_a_sourced_script_s_surface_is_its_functions_with_the_usage_above_each(
    tmp_path: Path,
) -> None:
    library = tmp_path / "lib.sh"
    _ = library.write_text(LIBRARY)
    assert bash.facts(library, tmp_path).surface == (
        Entry(
            "said",
            "`said`",
            (
                "`lib.sh:said`",
                "",
                "Usage: . lib.sh, then said <word>: says it.",
                "",
                "* `$1`",
                "* `$LOUD`",
            ),
        ),
        Entry("quiet", "`quiet`", ("`lib.sh:quiet`", "", "Heads-up: apart from said.")),
    )


def test_a_bats_file_has_no_surface(tmp_path: Path) -> None:
    tests = tmp_path / "run.bats"
    _ = tests.write_text(TESTS)
    assert bash.facts(tests, tmp_path).surface == ()
