import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import griffe

from .code import Code

# Compromise: what isn't Python is read by its strings and comments alone: a body in
# dollar quotes is read as SQL, as a function's body is, and an E'' string's \' throws
# the reading off.
_SCANNED = {
    ".sql": re.compile(
        r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|(--[^\n]*|/\*.*?\*/)", re.DOTALL
    ),
    ".toml": re.compile(
        r'"""(?:[^\\]|\\.)*?"""|\'\'\'.*?\'\'\'|"(?:[^"\\\n]|\\.)*"|\'[^\'\n]*\'|(#[^\n]*)',
        re.DOTALL,
    ),
}


@dataclass(frozen=True)
class _Comment:
    line: int
    column: int
    text: str
    alone: bool

    @property
    def last(self) -> int:
        return self.line + self.text.count("\n")


def _tokenized(source: str) -> list[_Comment]:
    return [
        _Comment(
            t.start[0], t.start[1], t.string.rstrip(), not t.line[: t.start[1]].strip()
        )
        for t in tokenize.generate_tokens(io.StringIO(source).readline)
        if t.type == tokenize.COMMENT
    ]


def _scanned(source: str, pattern: re.Pattern[str]) -> list[_Comment]:
    found: list[_Comment] = []
    for m in pattern.finditer(source):
        if m.group(1) is None:
            continue
        begun = source.rfind("\n", 0, m.start(1)) + 1
        found.append(
            _Comment(
                source.count("\n", 0, begun) + 1,
                m.start(1) - begun,
                m.group(1).rstrip(),
                not source[begun : m.start(1)].strip(),
            )
        )
    return found


def _blocks(found: list[_Comment]) -> list[list[_Comment]]:
    blocks: list[list[_Comment]] = []
    for c in found:
        last = blocks[-1][-1] if blocks else None
        if (
            last is not None
            and c.alone
            and last.alone
            and c.column == last.column
            and c.line == last.last + 1
        ):
            blocks[-1].append(c)
        else:
            blocks.append([c])
    return blocks


def _anchor(named: list[tuple[str, int, int, int]], block: list[_Comment]) -> str:
    first, last = block[0], block[-1]
    if first.alone:
        for name, begun, _, column in named:
            if begun == last.last + 1 and column == first.column:
                return name
    held = [
        (begun, name)
        for name, begun, ended, _ in named
        if begun <= first.line and last.last <= ended
    ]
    return max(held)[1] if held else ""


def _read(code: Code, path: Path) -> list[tuple[str, list[_Comment]]]:
    if path.suffix != ".py":
        scanned = _scanned(path.read_text(), _SCANNED[path.suffix])
        return [("", block) for block in _blocks(scanned)]
    file = code.file(path)
    return [
        (_anchor(file.names, block), block)
        for block in _blocks(_tokenized(file.source))
    ]


def _fenced(held: str) -> list[str]:
    fence = "`" * max([3, *(len(run) + 1 for run in re.findall("`+", held))])
    return [fence, *held.splitlines(), fence]


def _written(heading: list[str], held: dict[tuple[str, str], list[list[str]]]) -> str:
    lines = list(heading)
    for shown, anchor in sorted(held, key=lambda k: (k[0], k[1].casefold(), k[1])):
        lines += ["", f"## `{shown}:{anchor}`" if anchor else f"## `{shown}`"]
        for fenced in held[shown, anchor]:
            lines += ["", *fenced]
    return "\n".join(lines) + "\n"


def index(code: Code, package: str, repo: Path) -> str:
    directory = code.src.joinpath(*package.split("."))
    held: dict[tuple[str, str], list[list[str]]] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and (path.suffix == ".py" or path.suffix in _SCANNED):
            shown = str(path.relative_to(repo))
            for anchor, block in _read(code, path):
                fenced = _fenced("\n".join(c.text for c in block))
                held.setdefault((shown, anchor), []).append(fenced)
    return _written(
        [
            f"# Comments in `{package}`",
            "",
            "Written by `chatddx stamp write` from the comments in "
            + f"`{directory.relative_to(repo)}/`, each under its file and the name it is "
            + "in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).",
        ],
        held,
    )


def _tested(path: Path, directory: Path) -> bool:
    return (
        "test" in path.relative_to(directory).parts[:-1]
        or path.name == "conftest.py"
        or path.name.startswith("test_")
    )


def _claimed(code: Code, module: griffe.Module, node: ast.AST, whoops: str) -> bool:
    if isinstance(node, ast.Assert):
        return True
    if not isinstance(node, ast.Raise) or node.exc is None:
        return False
    target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
    kind = code.lookup(module, target)
    return kind is not None and code.subclass(kind, whoops)


def _claims(code: Code, path: Path, whoops: str) -> list[tuple[str, str]]:
    file = code.file(path)
    parts = path.relative_to(code.src).with_suffix("").parts
    module = code.get(".".join(parts[:-1] if parts[-1] == "__init__" else parts))
    assert isinstance(module, griffe.Module)
    found: list[tuple[int, int, str, str]] = []
    for node in ast.walk(file.tree):
        if isinstance(node, ast.stmt) and _claimed(code, module, node, whoops):
            last = node.end_lineno or node.lineno
            held = [
                (begun, name)
                for name, begun, ended, _ in file.names
                if begun <= node.lineno and last <= ended
            ]
            written = dedent(file.segment(node, padded=True) or "")
            anchor = max(held)[1] if held else ""
            found.append((node.lineno, node.col_offset, anchor, written))
    return [(anchor, written) for _, _, anchor, written in sorted(found)]


def whoopses(code: Code, package: str, repo: Path, whoops: str) -> str:
    directory = code.src.joinpath(*package.split("."))
    held: dict[tuple[str, str], list[list[str]]] = {}
    for path in sorted(directory.rglob("*.py")):
        if not _tested(path, directory):
            shown = str(path.relative_to(repo))
            for anchor, written in _claims(code, path, whoops):
                held.setdefault((shown, anchor), []).append(_fenced(written))
    return _written(
        [
            f"# Whoopses and asserts in `{package}`",
            "",
            "Written by `chatddx stamp write` from the `raise Whoops` and `assert` "
            + f"statements in `{directory.relative_to(repo)}/`, its tests left out, each "
            + "under its file and the name it is in; a stamp reads as in "
            + "[docs/surfaces.md](../surfaces.md).",
        ],
        held,
    )
