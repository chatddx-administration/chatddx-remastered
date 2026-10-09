from rich.text import Text

from chatddx.bench import PARTS, Cell
from chatddx.catalog.titles import short

from .shell import Repl


def use(repl: Repl, name: str) -> None:
    repl.cell = repl.bench.configuration(name, repl.cell)
    repl.say_changed()


def on(repl: Repl, name: str) -> None:
    repl.cell = repl.cell.on(name, repl.bench.endpoint(name))
    repl.say_changed()


def cell(repl: Repl, configuration: str, endpoint: str) -> None:
    on_it = Cell().on(endpoint, repl.bench.endpoint(endpoint))
    repl.cell = repl.bench.configuration(configuration, on_it)
    repl.say_changed()


def set_(repl: Repl, part: str, name: str) -> None:
    if part not in PARTS:
        repl.error(f"no part '{part}': {', '.join(PARTS)}")
        return

    if repl.cell.configuration is None:
        repl.error("the cell has no configuration to set it in: use CONFIGURATION")
        return

    changed = repl.cell.set(part, repl.bench.chunk(part, name, repl.cell), name)
    _ = repl.bench.skeleton(changed)
    repl.cell = changed
    repl.say_changed()


def save(repl: Repl, name: str) -> None:
    if repl.cell.configuration is None:
        repl.error("the cell has no configuration to save: use CONFIGURATION")
        return

    saved = repl.bench.save(repl.cell, name)
    repl.cell = saved.cell
    repl.forget()
    repl.console.print(Text(f"saved as {name}: {saved.what} {short(saved.digest)}"))
    repl.say_cell()
