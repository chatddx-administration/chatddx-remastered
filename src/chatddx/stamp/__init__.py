import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from chatddx import settings

from .code import Code
from .index import index, whoopses
from .markers import stamped, stamps
from .page import page
from .trace import Trace

__all__ = ["COMMENTS", "SURFACES", "WHOOPSES", "Proof", "check", "proofs", "write"]

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
    code = Code(settings.PROJECT_ROOT / "src", "chatddx")
    trace = Trace(code, _FINDING, _WHOOPS)
    found: list[Proof] = []
    for package in packages:
        name = f"chatddx.{package}"
        for path, written in (
            (
                SURFACES / f"{package}.md",
                page(code, trace, name, settings.PROJECT_ROOT),
            ),
            (COMMENTS / f"{package}.md", index(code, name, settings.PROJECT_ROOT)),
            (
                WHOOPSES / f"{package}.md",
                whoopses(code, name, settings.PROJECT_ROOT, _WHOOPS),
            ),
        ):
            current = path.read_text() if path.exists() else None
            try:
                found.append(Proof(path, current, stamped(current, written)))
            except ValueError as e:
                raise ValueError(f"{_shown(path)}: {e}") from None
    return found


def check(packages: Sequence[str], baseline: bool) -> None:
    flags: list[str] = []
    try:
        found = proofs(packages or settings.STAMPED)
    except ValueError as e:
        found, flags = [], [str(e)]
    if not packages:
        flags += [
            f"{_shown(p)}: no package of settings.STAMPED writes it"
            for p in sorted(
                [*SURFACES.glob("*.md"), *COMMENTS.glob("*.md"), *WHOOPSES.glob("*.md")]
            )
            if p.stem not in settings.STAMPED
        ]
    refused = bool(flags)
    behind = [s for s in found if s.behind]
    for s in found:
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
        found = proofs(packages or settings.STAMPED)
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
