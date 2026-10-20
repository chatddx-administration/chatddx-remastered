from collections.abc import Iterable
from pathlib import Path

from chatddx import settings

from .code import Code
from .markers import pending, signed, stamped
from .page import LEGEND, page
from .trace import Trace

__all__ = [
    "DOCS",
    "LEGEND",
    "Code",
    "Trace",
    "page",
    "pending",
    "regenerated",
    "signed",
    "stamped",
]

DOCS = settings.PROJECT_ROOT / "docs" / "reference"
FINDING = "chatddx.factors.base.Finding"


def regenerated(packages: Iterable[str]) -> dict[Path, str]:
    code = Code(settings.PROJECT_ROOT / "src", "chatddx")
    trace = Trace(code, FINDING)
    found = {DOCS / "README.md": LEGEND}
    for package in packages:
        path = DOCS / f"{package}.md"
        current = path.read_text() if path.exists() else None
        written = page(code, trace, f"chatddx.{package}", settings.PROJECT_ROOT)
        found[path] = stamped(current, written)
    return found
