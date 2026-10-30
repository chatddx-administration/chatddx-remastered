import json
import subprocess
from pathlib import Path
from typing import Any, cast

from .facts import Comment, Entry, Facts, Named

SUFFIXES = {".sh": "bash", ".bats": "bats"}
# Duplication: surface renders the entries this tells how to read.
LEGEND = [
    "```",
    "## `<script or function>`",
    "`<file>:<function>`",
    "",
    "<its usage, as the comment above it says>",
    "",
    "* `<command>`",
    "* `$<positional parameter>`",
    "* `$<variable from the environment>`",
    "```",
    "",
    "- A command, a script with a shebang or a top-level `case` on its first argument, is "
    + "an entry named after its file, its usage the comment it begins with, its commands "
    + "what that `case` dispatches; any other script is sourced, an entry for each of its "
    + "functions, its usage the comment right above it. A bats test is no entry.",
    "- The environment is what it reads in capitals and never assigns nor names, bash's "
    + "own, `PATH`, `HOME` and `PWD` left out.",
]
# Policy: what bash sets itself, or any environment holds, is no part of a script's surface.
_OWN = frozenset(
    {
        "BASH",
        "BASH_REMATCH",
        "BASH_SOURCE",
        "EPOCHREALTIME",
        "FUNCNAME",
        "HOME",
        "IFS",
        "LINENO",
        "OLDPWD",
        "PATH",
        "PIPESTATUS",
        "PWD",
        "RANDOM",
    }
)


def facts(path: Path, repo: Path) -> Facts:
    """The functions, tests, top-level assignments and comments of a bash or bats file,
    its shebang left out, as shfmt parses it, which runs once for it."""
    source = path.read_text()
    try:
        done = subprocess.run(
            ["shfmt", "-ln", SUFFIXES[path.suffix], "--to-json"],
            input=source,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"stamp: shfmt: {e.stderr.strip()}") from None
    lines = source.splitlines()
    tree: dict[str, Any] = json.loads(done.stdout)
    names = [
        _named(stmt, assigned["Name"]["Value"])
        for stmt in _listed(tree, "Stmts")
        if stmt["Cmd"].get("Type") == "CallExpr" and not stmt["Cmd"].get("Args")
        for assigned in _listed(stmt["Cmd"], "Assigns")
    ]
    comments: list[Comment] = []
    for node in _nodes(tree):
        for c in _listed(node, "Comments"):
            line, column = c["Hash"]["Line"], c["Hash"]["Col"] - 1
            if line == 1 and c["Text"].startswith("!"):
                continue
            alone = not lines[line - 1][:column].strip()
            comments.append(Comment(line, column, "#" + c["Text"].rstrip(), alone))
        if node.get("Type") == "FuncDecl":
            names.append(_named(node, node["Name"]["Value"]))
        elif node.get("Type") == "TestDecl":
            begun, ended = node["Description"]["Pos"], node["Description"]["End"]
            described = source.encode()[begun["Offset"] : ended["Offset"]].decode()
            names.append(_named(node, described.strip("'\"")))
    shown = str(path.relative_to(repo))
    ordered = tuple(sorted(set(comments), key=lambda c: (c.line, c.column)))
    return Facts(
        shown,
        tuple(sorted(names, key=lambda n: n.line)),
        ordered,
        (),
        () if path.suffix == ".bats" else surface(shown, source, tree, ordered),
    )


def surface(
    path: str, source: str, tree: dict[str, Any], comments: tuple[Comment, ...]
) -> tuple[Entry, ...]:
    """A script's entry, as a command, or its functions', as a script sourced."""
    statements = _listed(tree, "Stmts")
    dispatched = [
        _word(p)
        for stmt in statements
        if stmt["Cmd"].get("Type") == "CaseClause" and _first(stmt["Cmd"]["Word"])
        for item in _listed(stmt["Cmd"], "Items")
        for p in _listed(item, "Patterns")
        if _word(p) not in ("*", "")
    ]
    if source.startswith("#!") or dispatched:
        doc = _doc(comments, 2 if source.startswith("#!") else 1, None)
        bullets = [f"* `{c}`" for c in dispatched] + _environment(tree, tree)
        name = path.rpartition("/")[2]
        return (_entry(name, f"`{path}`", doc, bullets),)
    found: list[Entry] = []
    for stmt in statements:
        if stmt["Cmd"].get("Type") != "FuncDecl":
            continue
        function = stmt["Cmd"]
        name = function["Name"]["Value"]
        doc = _doc(comments, None, stmt["Pos"]["Line"])
        positional = sorted(
            {
                n["Param"]["Value"]
                for n in _nodes(function)
                if n.get("Type") == "ParamExp"
                and (n["Param"]["Value"].isdigit() or n["Param"]["Value"] in "@*#")
            }
        )
        bullets = [f"* `${p}`" for p in positional] + _environment(tree, function)
        found.append(_entry(name, f"`{path}:{name}`", doc, bullets))
    return tuple(found)


def _entry(name: str, location: str, doc: list[str], bullets: list[str]) -> Entry:
    lines = [location]
    if doc:
        lines += ["", *doc]
    if bullets:
        lines += ["", *bullets]
    return Entry(name, f"`{name}`", tuple(lines))


# Policy: a block of comments alone on their lines, its shellcheck directives left out:
# the one a script begins with, from its first line or the one after its shebang, or the
# one right above a function.
def _doc(
    comments: tuple[Comment, ...], begun: int | None, above: int | None
) -> list[str]:
    alone = {c.line: c for c in comments if c.alone and c.column == 0}
    line = begun if begun is not None else (above or 1) - 1
    held: list[Comment] = []
    while line in alone:
        held.append(alone[line])
        line += 1 if begun is not None else -1
    if begun is None:
        held.reverse()
    texts = [c.text.removeprefix("#").removeprefix(" ") for c in held]
    return [t for t in texts if not t.startswith("shellcheck ")]


def _environment(tree: dict[str, Any], within: dict[str, Any]) -> list[str]:
    nodes = _nodes(tree)
    assigns = [a for n in nodes for a in _listed(n, "Assigns")]
    assigns += [
        a for n in nodes if n.get("Type") == "DeclClause" for a in _listed(n, "Args")
    ]
    # Policy: an assignment that reads what it assigns, as X=${X:-x} does, takes it from
    # the environment still.
    assigned = {
        a["Name"]["Value"]
        for a in assigns
        if "Name" in a and a["Name"]["Value"] not in _read(a)
    }
    assigned |= {n["Name"]["Value"] for n in nodes if n.get("Type") == "WordIter"}
    named = {_word(w) for n in nodes for w in _listed(n, "Args")}
    return [
        f"* `${v}`"
        for v in sorted(_read(within))
        if v.isupper() and not v.isdigit() and v not in assigned | named | _OWN
    ]


def _read(node: dict[str, Any]) -> set[str]:
    return {n["Param"]["Value"] for n in _nodes(node) if n.get("Type") == "ParamExp"}


def _first(word: dict[str, Any]) -> bool:
    expanded = [n for n in _nodes(word) if n.get("Type") == "ParamExp"]
    return len(expanded) == 1 and expanded[0]["Param"]["Value"] == "1"


def _word(word: dict[str, Any]) -> str:
    return "".join(str(p.get("Value", "")) for p in _listed(word, "Parts"))


def _named(node: dict[str, Any], name: str) -> Named:
    return Named(name, node["Pos"]["Line"], node["End"]["Line"], node["Pos"]["Col"] - 1)


def _listed(node: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], node.get(key) or [])


def _nodes(tree: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    pending: list[Any] = [tree]
    while pending:
        held = pending.pop()
        if isinstance(held, dict):
            node = cast(dict[str, Any], held)
            found.append(node)
            pending += node.values()
        elif isinstance(held, list):
            pending += cast(list[Any], held)
    return found
