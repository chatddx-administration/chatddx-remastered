import subprocess
from collections.abc import Sequence
from pathlib import Path

from chatddx_dev import project

from .facts import Facts, loaded

SUFFIXES = (".ts", ".svelte")
EXTRACTOR = project.PROJECT_ROOT / "frontend" / "scripts" / "facts.mjs"
# Duplication: frontend/scripts/facts.mjs renders the entries this tells how to read.
LEGEND = [
    "```",
    "## `<name>` `async` `<<type parameters>>` `<extends or implements>` `<props' type>`",
    "`<file>:<qualified name>`",
    "",
    "<its JSDoc>",
    "",
    "* `<parameter, field or prop>: <type> = <default>`",
    "* ∟`<return type>`",
    "```",
    "",
    "- A module's entries are what it exports, a class's public members among them; a "
    + "component's is named after its file, its props its bullets, followed by what its "
    + "module script exports, and its heading gives its props' type only when the props "
    + "don't spell it out.",
    "- A type, an interface, an enum or a one-line constant is its declaration instead "
    + "of bullets, fenced as TypeScript once it takes more than a line; a longer constant "
    + "is its name, type and value.",
    "- A value that takes more than a line or 60 characters is cut to `…`, a call to its "
    + "callee's `(…)`.",
]


def facts(paths: Sequence[Path], repo: Path) -> list[Facts]:
    """The names and comments of TypeScript and Svelte files, as the frontend's
    extractor reads them with TypeScript's and Svelte's parsers, in one run of node."""
    if not paths:
        return []
    try:
        done = subprocess.run(
            ["node", str(EXTRACTOR)] + [str(p.relative_to(repo)) for p in paths],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"stamp: {EXTRACTOR.name}: {e.stderr.strip()}") from None
    return loaded(done.stdout)
