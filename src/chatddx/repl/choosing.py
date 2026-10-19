from rich.text import Text

from chatddx.catalog.titles import short
from chatddx.factors.request import RECIPE_PARTS

from .shell import NONE, Repl


def use(repl: Repl, name: str) -> None:
    variation = repl.bench.variation(name)
    repl.variation = variation
    if variation.recipe is not None:
        repl.under = None
    repl.say_changed(variation)


def under(repl: Repl, name: str) -> None:
    variation = repl.variation

    if variation is None:
        repl.error("the repl holds no configuration to run under it: use CONFIGURATION")
        return

    if variation.recipe is not None:
        repl.error(
            f"{variation.label} runs under its model's handle: set model {name} instead"
        )
        return

    repl.under = repl.bench.handle_named(name).name
    repl.say_changed(variation)


def set_(repl: Repl, part: str, name: str) -> None:
    if part not in RECIPE_PARTS:
        repl.error(f"no part '{part}': {', '.join(RECIPE_PARTS)}")
        return

    variation = repl.variation

    if variation is None:
        repl.error("the repl holds no configuration to set it in: use CONFIGURATION")
        return

    digest = None if name == NONE else repl.bench.thread(name, part)[0].digest
    changed = variation.set(part, digest, name)
    _ = repl.bench.skeleton(changed)
    repl.variation = changed
    repl.say_changed(changed)


def save(repl: Repl, name: str) -> None:
    variation = repl.variation

    if variation is None:
        repl.error("the repl holds no configuration to save: use CONFIGURATION")
        return

    saved = repl.bench.save(variation, name)
    repl.variation = repl.bench.variation(saved.edit.thread)
    repl.forget()
    repl.console.print(
        Text(f"saved as {name}: {saved.what} {short(saved.edit.digest)}")
    )
    _ = repl.say_variation(repl.variation)
