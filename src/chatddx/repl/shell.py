from collections.abc import Iterable

from rich.console import Console
from rich.text import Text

from chatddx.factors.base import Finding

from .bench import KINDS, NONE, OPTIONAL, PARTS, Bench, Cell, drawn_seed
from .render import REFUSED, finding


class Repl:
    def __init__(self, bench: Bench, console: Console, seed: int | None = None):
        self.bench: Bench = bench
        self.console: Console = console
        self.cell: Cell = Cell()
        self.seed: int = drawn_seed() if seed is None else seed
        self._completions: dict[str, list[str]] | None = None

    @property
    def prompt(self) -> str:
        cell = self.cell
        endpoint = f"×{cell.endpoint}" if cell.endpoint else ""
        held = f" {cell.label}{endpoint}" if cell.configuration or cell.endpoint else ""
        return f"{self.bench.person.login}{held} #{self.seed}> "

    # The names each word of a command can be: per-model names complete by their
    # name alone too, since the cell's endpoint picks the model.
    def completions(self) -> dict[str, list[str]]:
        if self._completions is not None:
            return self._completions
        bench = self.bench
        names = {word: self._per_model(bench.names(word)) for word in KINDS}
        for part in OPTIONAL:
            names[part] = [*names[part], NONE]
        names |= {
            "endpoint": sorted(bench.inventory.endpoints),
            "case": [f.name for f in bench.families()],
            "tag": bench.tags(),
            "part": [*PARTS],
            "kind": ["tag", "case", "endpoint", *KINDS],
        }
        self._completions = names
        return names

    def forget(self) -> None:
        self._completions = None

    def _per_model(self, names: list[str]) -> list[str]:
        alone = {
            name.removesuffix(f" ({model})")
            for name in names
            for model in self.bench.facts.models
            if name.endswith(f" ({model})")
        }
        return sorted({*names, *alone})

    def say_cell(self) -> None:
        configuration = self.cell.label or "?"
        endpoint = self.cell.endpoint or "?"
        self.console.print(Text(f"cell: {configuration} × {endpoint}"))

    # The cell as it changed, and what the lints say of its pair.
    def say_changed(self) -> None:
        self.say_cell()
        if self.cell.configuration is not None and self.cell.engine is not None:
            self.say_findings(self.bench.findings(self.cell, self.seed))

    def say_findings(self, findings: Iterable[Finding]) -> None:
        for f in findings:
            self.console.print(finding(f))

    def error(self, message: str) -> None:
        self.console.print(Text(message, style=REFUSED))
