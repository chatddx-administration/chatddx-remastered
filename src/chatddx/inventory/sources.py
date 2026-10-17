from pathlib import Path
from typing import Literal

from chatddx.factors.base import Fingerprint, Frozen
from chatddx.factors.cases import Case, CleanupOp, Vignette


class Source(Frozen):
    name: str
    sensitive: bool = True
    cleanup: tuple[CleanupOp, ...] = ()


class DatabaseSource(Source):
    kind: Literal["database"] = "database"


class DirectorySource(Source):
    kind: Literal["directory"] = "directory"
    path: Path
    suffix: str = ".txt"

    def ids(self) -> list[str]:
        return sorted(
            p.name.removesuffix(self.suffix)
            for p in self.path.iterdir()
            if p.is_file() and p.name.endswith(self.suffix)
        )

    def fetch(self, id: str) -> bytes:
        if "/" in id or "\\" in id or id.startswith("."):
            raise LookupError(f"case id {id!r} points outside source {self.name!r}")
        try:
            return (self.path / f"{id}{self.suffix}").read_bytes()
        except FileNotFoundError:
            raise LookupError(f"no case {id!r} in source {self.name!r}") from None

    def cases(self) -> list[Case]:
        return [
            Case(
                vignette=Vignette(
                    source=self.name, id=id, fingerprint=Fingerprint.of(self.fetch(id))
                )
            )
            for id in self.ids()
        ]
