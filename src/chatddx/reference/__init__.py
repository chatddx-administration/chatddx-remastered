from collections.abc import Iterable
from pathlib import Path

from chatddx import settings

from .code import Code
from .page import legend, page
from .tags import pending, tagged, untagged
from .trace import Trace

__all__ = [
    "DOCS",
    "Code",
    "Trace",
    "legend",
    "page",
    "pending",
    "regenerated",
    "tagged",
    "untagged",
]

DOCS = settings.PROJECT_ROOT / "docs" / "reference"
FINDING = "chatddx.factors.base.Finding"


def regenerated(packages: Iterable[str]) -> dict[Path, str]:
    code = Code(settings.PROJECT_ROOT / "src", "chatddx")
    trace = Trace(code, FINDING)
    found = {DOCS / "README.md": legend(settings.REFERENCE_TAG)}
    for package in packages:
        path = DOCS / f"{package}.md"
        current = path.read_text() if path.exists() else None
        written = page(code, trace, f"chatddx.{package}", settings.PROJECT_ROOT)
        found[path] = tagged(current, written, settings.REFERENCE_TAG)
    return found
