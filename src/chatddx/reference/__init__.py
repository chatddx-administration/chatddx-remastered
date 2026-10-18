from collections.abc import Iterable
from pathlib import Path

from chatddx import settings

from .index import Index
from .page import page
from .raises import Raises
from .tags import pending, tagged, untagged

__all__ = [
    "DOCS",
    "Index",
    "Raises",
    "page",
    "pending",
    "regenerated",
    "tagged",
    "untagged",
]

DOCS = settings.PROJECT_ROOT / "docs" / "reference"


def regenerated(packages: Iterable[str]) -> dict[Path, str]:
    index = Index(settings.PROJECT_ROOT / "src")
    raises = Raises(index)
    found: dict[Path, str] = {}
    for package in packages:
        path = DOCS / f"{package}.md"
        current = path.read_text() if path.exists() else None
        found[path] = tagged(current, page(index, raises, f"chatddx.{package}"))
    return found
