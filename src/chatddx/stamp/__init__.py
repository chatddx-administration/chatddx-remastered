import subprocess
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from chatddx import settings

from .code import Code
from .index import index, whoopses
from .markers import restamped, signed, stamped, stamps
from .page import page
from .trace import Trace

__all__ = [
    "COMMENTS",
    "SURFACES",
    "WHOOPSES",
    "Proof",
    "check",
    "docs",
    "documents",
    "proofs",
    "write",
]

SURFACES = settings.PROJECT_ROOT / "docs" / "surfaces"
COMMENTS = settings.PROJECT_ROOT / "docs" / "comments"
WHOOPSES = settings.PROJECT_ROOT / "docs" / "whoopses"
_FINDING = "chatddx.factors.base.Finding"
_WHOOPS = "chatddx.whoops.Whoops"


@dataclass(frozen=True)
class Proof:
    path: Path
    current: str | None
    written: str

    @property
    def behind(self) -> bool:
        return self.current != self.written

    @property
    def pending(self) -> int:
        return 0 if self.current is None else len(stamps(self.current))

    @property
    def new(self) -> int:
        held = Counter(stamps(self.current or ""))
        return (Counter(stamps(self.written)) - held).total()


def proofs(packages: Iterable[str]) -> list[Proof]:
    root = settings.PROJECT_ROOT
    code = Code(root / "src", "chatddx")
    trace = Trace(code, _FINDING, _WHOOPS)
    found: list[Proof] = []
    for package in packages:
        name = f"chatddx.{package}"
        if code.get(name) is None:
            continue
        for docs, write in (
            (SURFACES, partial(page, code, trace, name, root)),
            (COMMENTS, partial(index, code, name, root)),
            (WHOOPSES, partial(whoopses, code, name, root, _WHOOPS)),
        ):
            if settings.STAGES[package] < settings.STAMPED_FROM[docs.name]:
                continue
            path, written = docs / f"{package}.md", write()
            current = path.read_text() if path.exists() else None
            try:
                found.append(Proof(path, current, stamped(current, written)))
            except ValueError as e:
                raise ValueError(f"{_shown(path)}: {e}") from None
    return found


def documents() -> list[Path]:
    root, written = settings.PROJECT_ROOT, {SURFACES, COMMENTS, WHOOPSES}
    found = [p for p in (root / "docs").rglob("*.md") if not written & set(p.parents)]
    found += [*(root / "agents").glob("*.md"), root / "AGENTS.md", root / "README.md"]
    return sorted(p for p in found if p.is_file())


def check(packages: Sequence[str], baseline: bool) -> None:
    flags: list[str] = []
    try:
        found = proofs(packages or settings.STAGES)
        held = [] if packages else _held(documents())
    except ValueError as e:
        found, held, flags = [], [], [str(e)]
    else:
        if not packages:
            flags += _strays({s.path for s in found})
    refused = bool(flags)
    behind = [s for s in found if s.behind]
    for s in [*found, *held]:
        if baseline and s.behind:
            flags.append(
                f"{_shown(s.path)}: {_change(s)} at the baseline: the code changed "
                + "without chatddx stamp write; investigate before work proceeds"
            )
        elif baseline and s.pending:
            flags.append(
                f"{_shown(s.path)}: {_stamps(s.pending)} pending at the baseline: a "
                + "human stamps them before work proceeds"
            )
        elif s.pending and not behind:
            flags.append(f"{_shown(s.path)}: {_stamps(s.pending)} pending")
    for flag in flags:
        print(f"flag: {flag}", file=sys.stderr)
    if behind and not baseline:
        shown = ", ".join(_shown(s.path) for s in behind)
        raise SystemExit(f"stamp: {shown} behind the code: run chatddx stamp write")
    if refused or (baseline and flags):
        raise SystemExit(1)
    if not flags:
        print("ok")


def write(packages: Sequence[str]) -> None:
    try:
        found = proofs(packages or settings.STAGES)
    except ValueError as e:
        raise SystemExit(f"stamp write: {e}") from None
    written: list[str] = []
    for s in found:
        if not s.behind:
            continue
        s.path.parent.mkdir(parents=True, exist_ok=True)
        _ = s.path.write_text(s.written)
        written.append(
            f"{_shown(s.path)}: {'new' if s.current is None else _stamps(s.new)}"
        )
    print("\n".join(written) or "nothing to write")


def docs() -> None:
    root = settings.PROJECT_ROOT
    base, shown = _signed(root)
    ours = set(documents())
    print(f"against {shown}")
    written: list[str] = []
    for path, was in _changed(root, base):
        if path not in ours:
            continue
        current = path.read_text()
        then = None if was is None else _git(root, "show", f"{base}:{was}")
        try:
            s = Proof(path, current, restamped(then, current))
        except ValueError as e:
            raise SystemExit(f"stamp docs: {_shown(path)}: {e}") from None
        if s.behind:
            _ = path.write_text(s.written)
            written.append(f"{_shown(path)}: {_stamps(s.new)}")
    print("\n".join(written) or "nothing to write")


def _signed(root: Path) -> tuple[str, str]:
    mine = _git(root, "var", "GIT_AUTHOR_IDENT").rpartition("<")[2].partition(">")[0]
    for line in _git(
        root, "log", "--first-parent", "--format=%H %h %ae %s"
    ).splitlines():
        sha, short, author, subject = (line.split(" ", 3) + [""])[:4]
        if author != mine:
            return sha, f"{short} {subject}"
    raise SystemExit(
        f"stamp docs: no commit on HEAD's first parents is by anyone but {mine}, so "
        + "nothing says what a human signed"
    )


def _held(paths: Iterable[Path]) -> list[Proof]:
    found: list[Proof] = []
    for path in paths:
        text = path.read_text()
        try:
            _ = signed(text)
        except ValueError as e:
            raise ValueError(f"{_shown(path)}: {e}") from None
        found.append(Proof(path, text, text))
    return found


def _changed(root: Path, base: str) -> list[tuple[Path, str | None]]:
    found: list[tuple[Path, str | None]] = []
    fields = iter(_git(root, "diff", "-z", "--name-status", "-M", base).split("\0"))
    for status in fields:
        if status.startswith("R"):
            was = next(fields)
            found.append((root / next(fields), was))
        elif status in ("A", "M", "T"):
            name = next(fields)
            found.append((root / name, None if status == "A" else name))
        elif status:
            _ = next(fields)
    others = _git(root, "ls-files", "-z", "--others", "--exclude-standard")
    found += [(root / name, None) for name in others.split("\0") if name]
    return found


def _git(root: Path, *args: str) -> str:
    try:
        done = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"stamp docs: git {args[0]}: {e.stderr.strip()}") from None
    return done.stdout


def _strays(written: set[Path]) -> list[str]:
    src = settings.PROJECT_ROOT / "src" / "chatddx"
    modules = [p.parent for p in src.glob("*/__init__.py")]
    modules += [p for p in src.glob("*.py") if p.stem != "__init__"]
    docs = [*SURFACES.glob("*.md"), *COMMENTS.glob("*.md"), *WHOOPSES.glob("*.md")]
    return [
        f"{_shown(p)}: no stage in settings.STAGES"
        for p in sorted(modules)
        if p.stem not in settings.STAGES
    ] + [
        f"{_shown(p)}: no module writes it at its stage in settings.STAGES"
        for p in sorted(docs)
        if p not in written
    ]


def _shown(path: Path) -> str:
    return str(path.relative_to(settings.PROJECT_ROOT))


def _stamps(count: int) -> str:
    return f"{count} stamp" if count == 1 else f"{count} stamps"


def _change(proof: Proof) -> str:
    if proof.current is None:
        return "not written"
    if proof.new:
        return f"{proof.new} new {'stamp' if proof.new == 1 else 'stamps'}"
    return "behind the code"
