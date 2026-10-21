import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from chatddx import settings

from .code import Code
from .markers import stamped, stamps
from .page import page
from .trace import Trace

__all__ = ["DOCS", "Surface", "check", "surfaces", "write"]

DOCS = settings.PROJECT_ROOT / "docs" / "surfaces"
_FINDING = "chatddx.factors.base.Finding"


@dataclass(frozen=True)
class Surface:
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


def surfaces(packages: Iterable[str]) -> list[Surface]:
    code = Code(settings.PROJECT_ROOT / "src", "chatddx")
    trace = Trace(code, _FINDING)
    found: list[Surface] = []
    for package in packages:
        path = DOCS / f"{package}.md"
        current = path.read_text() if path.exists() else None
        written = page(code, trace, f"chatddx.{package}", settings.PROJECT_ROOT)
        try:
            found.append(Surface(path, current, stamped(current, written)))
        except ValueError as e:
            raise ValueError(f"{_shown(path)}: {e}") from None
    return found


def check(packages: Sequence[str], baseline: bool) -> None:
    flags: list[str] = []
    try:
        found = surfaces(packages or settings.STAMPED)
    except ValueError as e:
        found, flags = [], [str(e)]
    if not packages:
        flags += [
            f"{_shown(p)}: no package of settings.STAMPED writes it"
            for p in sorted(DOCS.glob("*.md"))
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
        found = surfaces(packages or settings.STAMPED)
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


def _change(surface: Surface) -> str:
    if surface.current is None:
        return "not written"
    if surface.new:
        return f"{surface.new} new {'stamp' if surface.new == 1 else 'stamps'}"
    return "behind the code"
