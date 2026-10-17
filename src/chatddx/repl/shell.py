import secrets
from collections.abc import Iterable
from dataclasses import dataclass, replace

from rich.console import Console
from rich.text import Text

from chatddx.bench import KINDS, Bench, Endpoint, TriedVariation
from chatddx.factors.base import Finding
from chatddx.factors.request import OPTIONAL_PARTS, RECIPE_PARTS

from .render import REFUSED, counted, finding

NONE = "none"

SEEDS = 100_000
MAX_SEED = 2**31 - 1


def drawn_seed() -> int:
    return secrets.randbelow(SEEDS)


# Names, vignettes and answers may hold brackets, which rich would read as markup.
def console(record: bool = False, width: int | None = None) -> Console:
    return Console(markup=False, record=record, width=width)


@dataclass(frozen=True)
class Cell:
    variation: TriedVariation | None = None
    endpoint: Endpoint | None = None

    def trying(self, variation: TriedVariation) -> "Cell":
        return replace(self, variation=variation)

    def on(self, endpoint: Endpoint | None) -> "Cell":
        return replace(self, endpoint=endpoint)

    @property
    def named(self) -> str | None:
        return None if self.endpoint is None else self.endpoint.name

    @property
    def label(self) -> str:
        return "" if self.variation is None else self.variation.label


class Repl:
    def __init__(self, bench: Bench, console: Console, seed: int | None = None):
        self.bench: Bench = bench
        self.console: Console = console
        self.cell: Cell = Cell()
        self.seed: int = drawn_seed() if seed is None else seed
        self.failed: bool = False
        self._completions: dict[str, list[str]] | None = None

    @property
    def prompt(self) -> str:
        cell, where = self.cell, self.where()
        endpoint = f"×{where}" if where else ""
        held = f" {cell.label}{endpoint}" if cell.label or where else ""
        return f"{self.bench.person.login}{held} #{self.seed}> "

    def where(self) -> str | None:
        cell = self.cell
        if cell.variation is None:
            return cell.named
        try:
            return self.bench.at(cell.variation, cell.named).name
        except (LookupError, ValueError):
            return cell.named

    @property
    def at(self) -> Endpoint | None:
        cell = self.cell
        if cell.endpoint is not None or cell.variation is None:
            return cell.endpoint
        try:
            return self.bench.at(cell.variation, None)
        except (LookupError, ValueError):
            return None

    @property
    def engine(self) -> str | None:
        at = self.at
        return None if at is None else at.engine

    def completions(self) -> dict[str, list[str]]:
        runs = self.bench.runs()[:20]
        return self._names() | {
            "replay:run": [str(r.run)[:8] for r in runs],
            "score:run": [str(r.run)[:8] for r, _ in self.bench.outstanding()],
        }

    def _names(self) -> dict[str, list[str]]:
        if self._completions is not None:
            return self._completions
        bench = self.bench
        names = {
            word: sorted({a.name for _, a in bench.threads(word) if a.name})
            for word in KINDS
        }
        for part in OPTIONAL_PARTS:
            names[f"set:{part}"] = [*names[part], NONE]
        families = bench.families()
        names |= {
            "endpoint": sorted(bench.inventory.endpoints),
            "case": [
                *(f.name for f in families),
                *sorted(bench.title(c) for f in families for c in f.cases[1:]),
            ],
            "tag": sorted({tag for f in families for tag in f.about.tags}),
            "part": [*RECIPE_PARTS],
            "kind": ["tag", "case", "endpoint", *KINDS],
        }
        self._completions = names
        return names

    def forget(self) -> None:
        self._completions = None

    def say_cell(self) -> None:
        configuration = self.cell.label or "?"
        endpoint = self.where() or "?"
        self.console.print(Text(f"cell: {configuration} × {endpoint}"))

    def say_changed(self) -> None:
        self.say_cell()
        cell = self.cell
        if cell.variation is not None and self.engine is not None:
            self.say_findings(
                self.bench.findings(cell.variation, self.engine, self.seed)
            )

    def say_findings(self, findings: Iterable[Finding], tally: bool = False) -> None:
        for f, times in counted(findings) if tally else ((f, 1) for f in findings):
            self.console.print(finding(f, times))

    def error(self, message: str) -> None:
        self.failed = True
        self.console.print(Text(message, style=REFUSED))
