import ast
import re
from collections import defaultdict
from functools import cache
from pathlib import Path
from textwrap import dedent

import pytest

from chatddx import settings

SRC = settings.PROJECT_ROOT / "src"
WORLD = SRC / "chatddx" / "test" / "world.py"
# Accommodating for the repl's tables: rich puts 3 spaces or more between columns, the
# repl's own layouts 2.
GAP = re.compile(r"\S {2,}\S")
# Accommodating for a regex's newline, written as the two characters \n.
LINES = re.compile(r"\n|\\n")
# Accommodating for plain words, which name other things too: a kind (judge), a level (off).
WORD = re.compile(r"[a-z]+")
SHARING = re.compile(r"(^|\.)(test_\w+|conftest)$")


@cache
def _tests() -> list[tuple[Path, ast.Module]]:
    return [
        (path, ast.parse(path.read_text()))
        for path in sorted(SRC.rglob("*.py"))
        if "test" in path.relative_to(SRC).parts
    ]


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


def _strings(node: ast.stmt) -> list[tuple[ast.Constant, str]]:
    if not isinstance(node, ast.Assign):
        return []
    held = node.value.elts if isinstance(node.value, ast.Tuple) else [node.value]
    return [
        (c, c.value)
        for c in held
        if isinstance(c, ast.Constant) and isinstance(c.value, str)
    ]


@pytest.mark.slow
def test_a_test_matches_a_table_s_cells_not_its_padding() -> None:
    padded = [
        f"{path.relative_to(SRC)}:{n}: {line!r}"
        for path, tree in _tests()
        for n, line in _asserted(tree)
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


@pytest.mark.slow
def test_a_name_tests_share_is_spelled_once_in_world_py() -> None:
    world = dict(_tests())[WORLD]
    spelled = {
        id(c): value
        for node in world.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
        for c, value in _strings(node)
        if not WORD.fullmatch(value)
    }
    again = [
        (WORLD, c)
        for c in ast.walk(world)
        if isinstance(c, ast.Constant)
        and c.value in spelled.values()
        and id(c) not in spelled
    ]
    again += [
        (path, c)
        for path, tree in _tests()
        if path != WORLD
        for node in tree.body
        for c, value in _strings(node)
        if value in spelled.values()
    ]
    assert not again, (
        "these spell a name again that chatddx.test.world spells; import it:\n"
        + "\n".join(f"{p.relative_to(SRC)}:{c.lineno}: {c.value!r}" for p, c in again)
    )


def _imported(node: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(node, ast.ImportFrom):
        return [node.module or ""]
    return [a.name for a in node.names]


def _written(node: ast.stmt) -> bool:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return not node.name.startswith("test_")
    if isinstance(node, ast.Assign):
        return not all(
            isinstance(t, ast.Name) and t.id.startswith("__") for t in node.targets
        )
    return isinstance(node, (ast.AnnAssign, ast.TypeAlias))


@pytest.mark.slow
def test_a_test_takes_what_it_shares_from_helpers_not_a_test_or_a_conftest() -> None:
    taken = [
        f"{path.relative_to(SRC)}:{node.lineno}: {name}"
        for path, tree in _tests()
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for name in _imported(node)
        if SHARING.search(name)
    ]
    assert not taken, (
        "these take from a test or a conftest; move what they share into a "
        + "test/helpers.py:\n"
        + "\n".join(taken)
    )


@pytest.mark.slow
def test_what_tests_share_is_written_once() -> None:
    written: defaultdict[str, list[str]] = defaultdict(list)
    for path, tree in _tests():
        for node in tree.body:
            if _written(node):
                written[ast.dump(node)].append(f"{path.relative_to(SRC)}:{node.lineno}")
    again = [", ".join(where) for where in written.values() if len(where) > 1]
    assert not again, (
        "these are written alike more than once; keep one in a test/helpers.py:\n"
        + "\n".join(again)
    )
