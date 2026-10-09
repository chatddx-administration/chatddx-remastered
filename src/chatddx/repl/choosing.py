from rich.text import Text

from chatddx.bench import PARTS
from chatddx.catalog.titles import short

from .shell import NONE, Cell, Repl


def use(repl: Repl, name: str) -> None:
    variation = repl.bench.configuration(name, repl.cell.engine)
    repl.cell = repl.cell.trying(variation)
    repl.say_changed()


def on(repl: Repl, name: str) -> None:
    repl.cell = repl.cell.on(name, repl.bench.endpoint(name))
    repl.say_changed()


def cell(repl: Repl, configuration: str, endpoint: str) -> None:
    on_it = Cell().on(endpoint, repl.bench.endpoint(endpoint))
    repl.cell = on_it.trying(repl.bench.configuration(configuration, on_it.engine))
    repl.say_changed()


def set_(repl: Repl, part: str, name: str) -> None:
    if part not in PARTS:
        repl.error(f"no part '{part}': {', '.join(PARTS)}")
        return

    variation = repl.cell.variation

    if variation is None:
        repl.error("the cell has no configuration to set it in: use CONFIGURATION")
        return

    digest = None if name == NONE else repl.bench.chunk(part, name, repl.cell.engine)
    changed = variation.set(part, digest, name)
    _ = repl.bench.skeleton(changed)
    repl.cell = repl.cell.trying(changed)
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
