import ast
import re
from textwrap import dedent

import pytest

from chatddx import settings

# Accommodating for the repl's tables: rich puts 3 spaces or more between columns, the
# repl's own layouts 2.
GAP = re.compile(r"\S {2,}\S")
# Accommodating for a regex's newline, written as the two characters \n.
LINES = re.compile(r"\n|\\n")


def _text(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(_text(v) or "x" for v in node.values)
    return None


def _asserted(tree: ast.Module) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        held = [e for e in ast.walk(node.test) if isinstance(e, ast.expr)]
        parts = {id(v) for e in held if isinstance(e, ast.JoinedStr) for v in e.values}
        for e in held:
            if id(e) not in parts and (text := _text(e)) is not None:
                found += [(e.lineno, line) for line in LINES.split(text)]
    return found


@pytest.mark.slow
def test_a_test_matches_a_table_s_cells_not_its_padding() -> None:
    src = settings.PROJECT_ROOT / "src"
    padded = [
        f"{path.relative_to(src)}:{n}: {line!r}"
        for path in sorted(src.rglob("*.py"))
        if "test" in path.relative_to(src).parts
        for n, line in _asserted(ast.parse(path.read_text()))
        if GAP.search(line)
    ]
    assert not padded, (
        "a longer name widens a table's padding, which these match; "
        + "match its cells instead (chatddx.repl.test.helpers.cells):\n"
        + "\n".join(padded)
    )


def test_padding_is_told_from_a_line_s_indent_and_an_f_string_s_values() -> None:
    source = dedent(
        """\
        assert "alice   3 runs" in said
        assert f"{name}   3 runs" in said
        assert re.search(r"differential\\n  1\\. Fake", said)
        assert "one two" in said
        """
    )
    found = _asserted(ast.parse(source))
    assert [n for n, line in found if GAP.search(line)] == [1, 2]
