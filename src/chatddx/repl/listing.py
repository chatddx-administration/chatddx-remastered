from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

from rich.table import Table
from rich.text import Text

from chatddx.bench import PARTS
from chatddx.catalog import language_of, made_for, variant_name
from chatddx.catalog.titles import short
from chatddx.inventory import url_of

from .render import LABEL, REFUSED, plural
from .shell import Repl


@dataclass(frozen=True)
class _Made:
    name: str
    base: str
    language: str | None
    model: str | None
    thread: int
    owner: int | None
    parts: list[str | None] | None


def configurations(repl: Repl, name: str | None = None) -> None:
    bench = repl.bench
    models = list(bench.facts.models)
    made: list[_Made] = []
    heads = bench.threads("configuration")

    for edit, about in heads:
        recipe = bench.catalog.recipe(edit.thread)
        parts = None if recipe is None else [getattr(recipe, p) for p in PARTS]
        full = about.name or bench.catalog.title(edit.thread)
        base, language, model = made_for(full, models) or (full, None, None)
        made.append(_Made(full, base, language, model, edit.thread, about.owner, parts))

    if name is None:
        judging = {e.thread for e, _ in bench.purposed(heads, "judge")}
        _grouped(repl, [m for m in made if m.thread not in judging], models)
        if judges := [m for m in made if m.thread in judging]:
            repl.console.print(Text("\njudge configurations", style="bold"))
            _grouped(repl, judges, models)
        return

    base, language = language_of(name)
    found = [
        m
        for m in made
        if name == m.name or (m.base == base and language in (None, m.language))
    ]

    if not found:
        repl.error(f"no configuration {name!r} for {bench.person.login}")
        return

    rows = [
        (m.name, bench.login(m.owner) if m.owner != bench.person.id else "", m.parts)
        for m in found
    ]
    _table(repl, rows, cache(bench.title))


def _grouped(repl: Repl, made: list[_Made], models: list[str]) -> None:
    bench = repl.bench
    groups: dict[tuple[str, str | None, int | None], list[_Made]] = {}

    for m in made:
        groups.setdefault((m.base, m.language, m.owner), []).append(m)

    forked = {
        origin: m.thread
        for m in made
        if m.owner == bench.person.id
        if (origin := bench.catalog.origin(m.thread)) is not None
    }
    title = cache(bench.title)
    rows: list[tuple[str, str, list[str | None] | None, str]] = []

    for (base, language, owner), held in groups.items():
        if owner != bench.person.id and all(m.thread in forked for m in held):
            continue
        threads = {m.thread for m in held}
        origins = {
            bench.login(by)
            for origin, thread in forked.items()
            if thread in threads
            if (by := bench.about(origin).owner) != bench.person.id
        }
        said = "yours" if owner == bench.person.id else bench.login(owner)
        if origins:
            said += f", from {', '.join(sorted(origins))}"
        on = sorted({_short(m.model) for m in held if m.model}, key=str.casefold)
        rows.append(
            (
                variant_name(base, language, None),
                said,
                _alike([m.parts for m in held], title, models),
                "\n".join(on) or "every model",
            )
        )

    shown = _shown([parts for _, _, parts, _ in rows])
    table = Table(box=None, header_style="bold")

    table.add_column("configuration", no_wrap=True)
    table.add_column("models", no_wrap=True, max_width=14)

    for i in shown:
        table.add_column(PARTS[i])

    table.add_column("owner", no_wrap=True)

    for name, owner, parts, on in sorted(rows, key=lambda r: (r[0], r[1])):
        if parts is None:
            cells = [Text("no recipe", style=LABEL), *([""] * (len(shown) - 1))]
        else:
            cells = [parts[i] or "—" for i in shown]
        table.add_row(name, on, *cells, owner)

    repl.console.print(table)


def _alike(
    held: list[list[str | None] | None],
    title: Callable[[str | None], str],
    models: list[str],
) -> list[str | None] | None:
    if any(parts is None for parts in held):
        return None
    alike: list[str | None] = []
    for i in range(len(PARTS)):
        titles = {_unmodelled(title(p[i]), models) for p in held if p and p[i]}
        alike.append(
            None if not titles else titles.pop() if len(titles) == 1 else "varies"
        )
    return alike


def _unmodelled(name: str, models: list[str]) -> str:
    made = made_for(name, models)
    if made is None or made[2] is None:
        return name
    return variant_name(made[0], made[1], None)


def _short(model: str) -> str:
    return model.rpartition("/")[2]


def _shown(rows: list[list[str | None] | None]) -> list[int]:
    return [
        i
        for i in range(len(PARTS))
        if any(parts and parts[i] is not None for parts in rows)
    ]


def _table(
    repl: Repl,
    rows: list[tuple[str, str, list[str | None] | None]],
    title: Callable[[str | None], str],
) -> None:
    shown = _shown([parts for _, _, parts in rows])
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
