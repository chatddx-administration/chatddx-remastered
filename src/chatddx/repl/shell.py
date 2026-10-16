import secrets
from collections.abc import Iterable
from dataclasses import dataclass, replace

from rich.console import Console
from rich.text import Text

from chatddx.bench import KINDS, OPTIONAL, PARTS, Bench, TriedVariation
from chatddx.factors.base import Finding

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
    endpoint: str | None = None
    served: str | None = None

    def trying(self, variation: TriedVariation) -> "Cell":
        return replace(self, variation=variation)

    def on(self, endpoint: str | None, served: str | None) -> "Cell":
        return replace(self, endpoint=endpoint, served=served)

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
            return cell.endpoint
        try:
            return self.bench.at(cell.variation, cell.endpoint)[0]
        except (LookupError, ValueError):
            return cell.endpoint

    # The engine the cell's configuration is rendered and linted for: the endpoint's,
    # else the one serving the configuration's model.
    @property
    def engine(self) -> str | None:
        cell = self.cell
        if cell.served is not None or cell.variation is None:
            return cell.served
        try:
            return self.bench.at(cell.variation, None)[1]
        except (LookupError, ValueError):
            return None

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
        names = {word: bench.names(word) for word in KINDS}
        for part in OPTIONAL:
            names[f"set:{part}"] = [*names[part], NONE]
        names |= {
            "endpoint": sorted(bench.inventory.endpoints),
            "case": [*(f.name for f in bench.families()), *bench.case_titles()],
            "tag": bench.tags(),
            "part": [*PARTS],
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
