from rich.text import Text

from chatddx.bench import PARTS, NotFound, TriedVariation
from chatddx.catalog.titles import short

from .render import LABEL, LATER
from .shell import NONE, Cell, Repl


def use(repl: Repl, name: str) -> None:
    try:
        variation = repl.bench.configuration(name, repl.cell.engine)
    except NotFound as e:
        if repl.cell.engine is not None or not e.per_model:
            raise
        repl.cell = repl.cell.holding(name)
        repl.console.print(
            Text(f"{name} is made per model: on ENDPOINT picks its variant", LABEL)
        )
        repl.say_changed()
        return
    repl.cell = repl.cell.trying(variation, name)
    repl.say_changed()


def on(repl: Repl, name: str) -> None:
    cell = repl.cell.on(name, repl.bench.endpoint(name))
    repl.cell = cell if cell.name is None else _picked(repl, cell)
    repl.say_changed()


def cell(repl: Repl, configuration: str, endpoint: str) -> None:
    on_it = Cell().on(endpoint, repl.bench.endpoint(endpoint))
    variation = repl.bench.configuration(configuration, on_it.engine)
    repl.cell = on_it.trying(variation, configuration)
    repl.say_changed()


def _picked(repl: Repl, cell: Cell) -> Cell:
    bench, held = repl.bench, cell.variation
    assert cell.name is not None and cell.engine is not None
    try:
        picked = _again(repl, cell.name, cell.engine, held)
    except LookupError as e:
        if held is None:
            raise
        repl.console.print(Text(f"{e}; the cell keeps {held.label}", LATER))
        return cell
    if held is None or picked.configuration.thread != held.configuration.thread:
        model = bench.model(cell.engine) or cell.endpoint
        repl.console.print(Text(f"{cell.name} on {model}: {picked.label}", LABEL))
    return cell.trying(picked)


def _again(
    repl: Repl, name: str, engine: str, held: TriedVariation | None
) -> TriedVariation:
    bench = repl.bench
    picked = bench.configuration(name, engine)
    for part, (_, said) in () if held is None else held.parts.items():
        digest = None if said == NONE else bench.chunk(part, said, engine)
        picked = picked.set(part, digest, said)
    return picked


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
    repl.cell = repl.cell.trying(saved.variation, name)
    repl.forget()
    repl.console.print(Text(f"saved as {name}: {saved.what} {short(saved.digest)}"))
    repl.say_cell()
