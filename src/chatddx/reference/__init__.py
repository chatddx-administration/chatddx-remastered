from collections.abc import Iterable
from pathlib import Path

from chatddx import settings

from .code import Code
from .page import page
from .raises import Raises
from .tags import pending, tagged, untagged

__all__ = [
    "DOCS",
    "Code",
    "Raises",
    "page",
    "pending",
    "regenerated",
    "tagged",
    "untagged",
]

DOCS = settings.PROJECT_ROOT / "docs" / "reference"


def regenerated(packages: Iterable[str]) -> dict[Path, str]:
    code = Code(settings.PROJECT_ROOT / "src", "chatddx")
    raises = Raises(code)
    found: dict[Path, str] = {}
    for package in packages:
        path = DOCS / f"{package}.md"
        current = path.read_text() if path.exists() else None
        written = page(code, raises, f"chatddx.{package}", settings.PROJECT_ROOT)
        found[path] = tagged(current, written)
    return found
