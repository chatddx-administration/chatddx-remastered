from collections import Counter
from functools import cache

from rich.table import Table
from rich.text import Text

from chatddx.catalog.titles import short
from chatddx.inventory import url_of

from .bench import PARTS
from .render import LABEL, REFUSED, plural
from .shell import Repl


def configurations(repl: Repl) -> None:
    bench = repl.bench
    title = cache(bench.title)
    rows: list[tuple[str, str, list[str | None] | None]] = []

    for edit, about in bench.threads("configuration"):
        recipe = bench.catalog.recipe(edit.thread)
        parts = None if recipe is None else [getattr(recipe, p) for p in PARTS]
        name = about.name or bench.catalog.title(edit.thread)
        rows.append((name, bench.owner(about), parts))

    shown = [
        i
        for i in range(len(PARTS))
        if any(parts and parts[i] is not None for _, _, parts in rows)
    ]
    table = Table(box=None, header_style="bold")

    for column in ("configuration", *(PARTS[i] for i in shown), "owner"):
        table.add_column(column)

    for name, owner, parts in sorted(rows, key=lambda r: (r[0], r[1])):
        if parts is None:
            cells = [Text("no recipe", style=LABEL), *([""] * (len(shown) - 1))]
        else:
            cells = [title(parts[i]) for i in shown]
        table.add_row(name, *cells, owner)

    repl.console.print(table)


def endpoints(repl: Repl) -> None:
    bench = repl.bench
    table = Table(box=None, header_style="bold")

    for column in ("endpoint", "engine", "model", "url", "cleared for"):
        table.add_column(column)

    for name, spec in sorted(bench.inventory.endpoints.items()):
        cleared = " ".join(sorted(bench.inventory.cleared_for(name))) or "—"
        try:
            engine = bench.endpoint(name)
        except LookupError:
            said = Text(f"{short(spec.engine)}, not in the store", style=REFUSED)
            table.add_row(name, said, "", str(spec.url or "—"), cleared)
            continue
        try:
            url = Text(url_of(bench.inventory, bench.get, name))
        except LookupError as e:
            url = Text(str(e), style=REFUSED)
        table.add_row(
            name, bench.title(engine), bench.model(engine) or "—", url, cleared
        )

    repl.console.print(table)


def cases(repl: Repl) -> None:
    families = repl.bench.families()
    repl.console.print(Text("  ".join(f.name for f in families)))
    tags = Counter(tag for f in families for tag in f.about.tags)
    tagged = ", ".join(f"{tag} {n}" for tag, n in sorted(tags.items()))
    said = plural(len(families), "case") + (f"; tagged {tagged}" if tagged else "")
    repl.console.print(said, style=LABEL)
