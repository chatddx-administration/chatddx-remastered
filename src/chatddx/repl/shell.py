import secrets
from collections.abc import Iterable

from rich.console import Console
from rich.text import Text

from chatddx.bench import KINDS, Bench, Endpoint, TriedVariation
from chatddx.factors.base import Finding
from chatddx.factors.request import OPTIONAL_PARTS, RECIPE_PARTS

from .render import LATER, REFUSED, counted, finding

NONE = "none"

SEEDS = 100_000
MAX_SEED = 2**31 - 1


def drawn_seed() -> int:
    return secrets.randbelow(SEEDS)


# Names, vignettes and answers may hold brackets, which rich would read as markup.
def console(record: bool = False, width: int | None = None) -> Console:
    return Console(markup=False, record=record, width=width)


class Repl:
    def __init__(self, bench: Bench, console: Console, seed: int | None = None):
        self.bench: Bench = bench
        self.console: Console = console
        self.variation: TriedVariation | None = None
        self.under: str | None = None
        self.seed: int = drawn_seed() if seed is None else seed
        self.failed: bool = False
        self._completions: dict[str, list[str]] | None = None

    @property
    def prompt(self) -> str:
        label = "" if self.variation is None else self.variation.label
        under = f"×{self.under}" if self.under else ""
        held = f" {label}{under}" if label or under else ""
        return f"{self.bench.person.login}{held} #{self.seed}> "

    @property
    def at(self) -> Endpoint | None:
        if self.variation is None:
            return None
        try:
            return self.bench.at(self.variation, model=self.under)
        except (LookupError, ValueError):
            return None

    @property
    def engine(self) -> str | None:
        at = self.at
        return None if at is None else at.engine

    def handle(self, at: Endpoint) -> str:
        return self.bench.handle(at.model.digest).name

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

    def say_variation(self, variation: TriedVariation) -> Endpoint | None:
        try:
            at = self.bench.at(variation, model=self.under)
            handle = self.handle(at)
        except (LookupError, ValueError) as e:
            self.console.print(Text(f"variation: {variation.label} × ?"))
            self.console.print(Text(str(e), style=LATER))
            return None
        self.console.print(Text(f"variation: {variation.label} × {handle}"))
        return at

    def say_changed(self, variation: TriedVariation) -> None:
        if (at := self.say_variation(variation)) is not None:
            self.say_findings(self.bench.findings(variation, at.engine, self.seed))

    def say_findings(self, findings: Iterable[Finding], tally: bool = False) -> None:
        for f, times in counted(findings) if tally else ((f, 1) for f in findings):
            self.console.print(finding(f, times))

    def error(self, message: str) -> None:
        self.failed = True
        self.console.print(Text(message, style=REFUSED))
