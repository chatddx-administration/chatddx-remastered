from .bench import MAX_SEED, drawn_seed
from .render import LABEL
from .shell import Repl


def seed(repl: Repl, value: str | None = None) -> None:
    if value is None:
        repl.seed = drawn_seed()
    elif not (value.isascii() and value.isdigit()) or int(value) > MAX_SEED:
        repl.error(f"a seed is a whole number from 0 to {MAX_SEED}, not {value}")
        return
    else:
        repl.seed = int(value)

    repl.console.print(f"seed: #{repl.seed}")
    cell = repl.cell

    if cell.configuration is not None and repl.bench.skeleton(cell).greedy:
        repl.console.print("greedy: the seed isn't sent", style=LABEL)
