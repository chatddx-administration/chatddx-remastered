from rich.text import Text

from chatddx.bench import TriedVariation
from chatddx.catalog.titles import short
from chatddx.factors.base import StructuralError
from chatddx.factors.request import RECIPE_PARTS

from .render import LATER
from .shell import NONE, Cell, Repl


def use(repl: Repl, name: str) -> None:
    variation = repl.bench.variation(name)
    repl.cell = repl.cell.trying(_served(repl, repl.cell, variation))
    _changed(repl)


def on(repl: Repl, name: str) -> None:
    cell = repl.cell.on(repl.bench.endpoint(name))
    if cell.variation is not None:
        cell = cell.trying(_served(repl, cell, cell.variation))
    repl.cell = cell
    _changed(repl)


def cell(repl: Repl, configuration: str, endpoint: str) -> None:
    on_it = Cell().on(repl.bench.endpoint(endpoint))
    variation = repl.bench.variation(configuration)
    repl.cell = on_it.trying(_served(repl, on_it, variation))
    _changed(repl)


def _served(repl: Repl, cell: Cell, variation: TriedVariation) -> TriedVariation:
    if cell.endpoint is None or variation.recipe is None:
        return variation
    model = cell.endpoint.model
    return variation.set("model", model.digest, repl.bench.title(model.digest))


# The cell takes the model even where it refuses a pick, so that a set mends it.
def _changed(repl: Repl) -> None:
    try:
        repl.say_changed()
    except StructuralError as e:
        repl.console.print(Text(f"{e}: set another in its place", style=LATER))


def set_(repl: Repl, part: str, name: str) -> None:
    if part not in RECIPE_PARTS:
        repl.error(f"no part '{part}': {', '.join(RECIPE_PARTS)}")
        return

    variation = repl.cell.variation

    if variation is None:
        repl.error("the cell has no configuration to set it in: use CONFIGURATION")
        return

    digest = None if name == NONE else repl.bench.thread(name, part)[0].digest
    changed = variation.set(part, digest, name)
    _ = repl.bench.skeleton(changed)
    cell = repl.cell.trying(changed)
    at = cell.endpoint
    if part == "model" and at is not None and at.model.digest != digest:
        cell = cell.on(None)
    repl.cell = cell
    repl.say_changed()


def save(repl: Repl, name: str) -> None:
    variation = repl.cell.variation

    if variation is None:
        repl.error("the cell has no configuration to save: use CONFIGURATION")
        return

    saved = repl.bench.save(variation, name)
    repl.cell = repl.cell.trying(repl.bench.variation(saved.edit.thread))
    repl.forget()
    repl.console.print(
        Text(f"saved as {name}: {saved.what} {short(saved.edit.digest)}")
    )
    repl.say_cell()
