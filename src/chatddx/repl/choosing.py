from rich.text import Text

from chatddx.bench import PARTS, TriedVariation
from chatddx.catalog.titles import short

from .shell import NONE, Cell, Repl


def use(repl: Repl, name: str) -> None:
    variation = repl.bench.configuration(name)
    repl.cell = repl.cell.trying(_served(repl, repl.cell, variation))
    repl.say_changed()


def on(repl: Repl, name: str) -> None:
    cell = repl.cell.on(name, repl.bench.endpoint(name))
    if cell.variation is not None:
        cell = cell.trying(_served(repl, cell, cell.variation))
    repl.cell = cell
    repl.say_changed()


def cell(repl: Repl, configuration: str, endpoint: str) -> None:
    on_it = Cell().on(endpoint, repl.bench.endpoint(endpoint))
    variation = repl.bench.configuration(configuration)
    repl.cell = on_it.trying(_served(repl, on_it, variation))
    repl.say_changed()


def _served(repl: Repl, cell: Cell, variation: TriedVariation) -> TriedVariation:
    if cell.served is None or variation.recipe is None:
        return variation
    return variation.set("engine", cell.served, repl.bench.title(cell.served))


def set_(repl: Repl, part: str, name: str) -> None:
    if part not in PARTS:
        repl.error(f"no part '{part}': {', '.join(PARTS)}")
        return

    variation = repl.cell.variation

    if variation is None:
        repl.error("the cell has no configuration to set it in: use CONFIGURATION")
        return

    digest = None if name == NONE else repl.bench.chunk(part, name)
    changed = variation.set(part, digest, name)
    _ = repl.bench.skeleton(changed)
    cell = repl.cell.trying(changed)
    if part == "engine" and cell.served not in (None, digest):
        cell = cell.on(None, None)
    repl.cell = cell
    repl.say_changed()


def save(repl: Repl, name: str) -> None:
    variation = repl.cell.variation

    if variation is None:
        repl.error("the cell has no configuration to save: use CONFIGURATION")
        return

    saved = repl.bench.save(variation, name)
    repl.cell = repl.cell.trying(saved.variation)
    repl.forget()
    repl.console.print(Text(f"saved as {name}: {saved.what} {short(saved.digest)}"))
    repl.say_cell()
