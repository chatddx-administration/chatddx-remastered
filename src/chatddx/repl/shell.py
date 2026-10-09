import secrets
from collections.abc import Iterable
from dataclasses import dataclass, replace

from rich.console import Console
from rich.text import Text

from chatddx.bench import KINDS, OPTIONAL, PARTS, Bench, TriedVariation
from chatddx.factors.base import Finding

from .render import REFUSED, finding

# What `set` takes an optional part out with.
NONE = "none"

# A drawn seed is short, so the prompt stays readable; any seed a trial takes can be held.
SEEDS = 100_000
MAX_SEED = 2**31 - 1


def drawn_seed() -> int:
    return secrets.randbelow(SEEDS)


# What the repl runs: a configuration, or a variation of it being tried, at an endpoint,
# with the engine the endpoint serves. Either side can be missing.
@dataclass(frozen=True)
class Cell:
    variation: TriedVariation | None = None
    endpoint: str | None = None
    engine: str | None = None

    def trying(self, variation: TriedVariation) -> "Cell":
        return replace(self, variation=variation)

    def on(self, endpoint: str, engine: str) -> "Cell":
        return replace(self, endpoint=endpoint, engine=engine)

    @property
    def label(self) -> str:
        return "" if self.variation is None else self.variation.label


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
        held = f" {cell.label}{endpoint}" if cell.variation or cell.endpoint else ""
        return f"{self.bench.person.login}{held} #{self.seed}> "

    # The names each word of a command can be: per-model names complete by their
    # name alone too, since the cell's endpoint picks the model. Runs come fresh.
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
        cell = self.cell
        if cell.variation is not None and cell.engine is not None:
            self.say_findings(
                self.bench.findings(cell.variation, cell.engine, self.seed)
            )

    def say_findings(self, findings: Iterable[Finding]) -> None:
        for f in findings:
            self.console.print(finding(f))

    def error(self, message: str) -> None:
        self.console.print(Text(message, style=REFUSED))
