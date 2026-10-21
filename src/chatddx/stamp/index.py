import ast
import io
import re
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

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


def _assigned(node: ast.AST) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return node.name.id if isinstance(node, ast.TypeAlias) else None


def _named(
    node: ast.AST, prefix: str, fields: bool
) -> Iterator[tuple[str, int, int, int]]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = prefix + child.name
            first = min([child.lineno, *(d.lineno for d in child.decorator_list)])
            yield name, first, child.end_lineno or first, child.col_offset
            yield from _named(child, f"{name}.", isinstance(child, ast.ClassDef))
        elif fields and isinstance(child, ast.stmt) and (name := _assigned(child)):
            yield (
                prefix + name,
                child.lineno,
                child.end_lineno or child.lineno,
                child.col_offset,
            )
        else:
            yield from _named(child, prefix, fields)


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


def _read(path: Path) -> list[tuple[str, list[_Comment]]]:
    source = path.read_text()
    if path.suffix != ".py":
        return [
            ("", block) for block in _blocks(_scanned(source, _SCANNED[path.suffix]))
        ]
    named = list(_named(ast.parse(source, str(path)), "", fields=True))
    return [(_anchor(named, block), block) for block in _blocks(_tokenized(source))]


def _fenced(block: list[_Comment]) -> list[str]:
    held = "\n".join(c.text for c in block)
    fence = "`" * max([3, *(len(run) + 1 for run in re.findall("`+", held))])
    return [fence, *held.splitlines(), fence]


def index(src: Path, package: str, repo: Path) -> str:
    directory = src.joinpath(*package.split("."))
    held: dict[tuple[str, str], list[list[str]]] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and (path.suffix == ".py" or path.suffix in _SCANNED):
            shown = str(path.relative_to(repo))
            for anchor, block in _read(path):
                held.setdefault((shown, anchor), []).append(_fenced(block))
    lines = [
        f"# Comments in `{package}`",
        "",
        "Written by `chatddx stamp write` from the comments in "
        + f"`{directory.relative_to(repo)}/`, each under its file and the name it is in "
        + "or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).",
    ]
    for shown, anchor in sorted(held, key=lambda k: (k[0], k[1].casefold(), k[1])):
        lines += ["", f"## `{shown}:{anchor}`" if anchor else f"## `{shown}`"]
        for fenced in held[shown, anchor]:
            lines += ["", *fenced]
    return "\n".join(lines) + "\n"
