from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

from rich.table import Table
from rich.text import Text

from chatddx.bench import Bench
from chatddx.catalog import Subject, read, threads, titles
from chatddx.catalog.language import edit_languages
from chatddx.catalog.titles import short
from chatddx.factors.request import RECIPE_PARTS, Recipe, translated

from .render import LABEL, REFUSED, plural
from .shell import Repl


@dataclass(frozen=True)
class _Made:
    name: str
    languages: tuple[str, ...]
    thread: int
    owner: int | None
    parts: list[str | None] | None


def configurations(repl: Repl, name: str | None = None) -> None:
    bench = repl.bench
    made: list[_Made] = []
    heads = bench.threads("configuration")
    own = edit_languages(bench.rows, [e for e, _ in heads])

    for edit, about in heads:
        recipe = threads.recipe(bench.rows, edit)
        parts = None if recipe is None else [getattr(recipe, p) for p in RECIPE_PARTS]
        full = about.name or titles.title(bench.rows, edit.thread)
        held = own[edit.id]
        languages = tuple([] if held is None else [held]) + tuple(
            lang for lang in _translated(bench, recipe) if lang != held
        )
        made.append(_Made(full, languages, edit.thread, about.owner, parts))

    if name is None:
        judges = bench.threads("configuration", purpose="judge")
        judging = {e.thread for e, _ in judges}
        _grouped(repl, [m for m in made if m.thread not in judging])
        if judges := [m for m in made if m.thread in judging]:
            repl.console.print(Text("\njudge configurations", style="bold"))
            _grouped(repl, judges)
        return

    found = [m for m in made if m.name == name]

    if not found:
        repl.error(f"no configuration {name!r} for {bench.person.login}")
        return

    rows = [
        (
            m.name,
            _languages([m.languages]),
            bench.login(m.owner) if m.owner != bench.person.id else "",
            m.parts,
        )
        for m in found
    ]
    _table(repl, rows, _title(bench))


def _title(bench: Bench) -> Callable[[str | None], str]:
    @cache
    def title(digest: str | None) -> str:
        return "—" if digest is None else bench.title(digest)

    return title


def _translated(bench: Bench, recipe: Recipe | None) -> list[str]:
    return [] if recipe is None else list(translated(recipe, bench.store.get))


def _grouped(repl: Repl, made: list[_Made]) -> None:
    bench = repl.bench
    groups: dict[tuple[str, int | None], list[_Made]] = {}

    for m in made:
        groups.setdefault((m.name, m.owner), []).append(m)

    forked = {
        origin: m.thread
        for m in made
        if m.owner == bench.person.id
        if (origin := threads.origin(bench.rows, m.thread)) is not None
    }
    title = _title(bench)
    rows: list[tuple[str, str, str, list[str | None] | None]] = []

    for (name, owner), held in groups.items():
        if owner != bench.person.id and all(m.thread in forked for m in held):
            continue
        ids = {m.thread for m in held}
        origins = {
            bench.login(by)
            for origin, thread in forked.items()
            if thread in ids
            if (by := read.about(bench.rows, Subject(thread=origin)).owner)
            != bench.person.id
        }
        said = "yours" if owner == bench.person.id else bench.login(owner)
        if origins:
            said += f", from {', '.join(sorted(origins))}"
        rows.append(
            (
                name,
                _languages([m.languages for m in held]),
                said,
                _alike([m.parts for m in held], title),
            )
        )

    shown = _shown([parts for _, _, _, parts in rows])
    table = Table(box=None, header_style="bold")

    table.add_column("configuration", no_wrap=True)
    table.add_column("languages", no_wrap=True)

    for i in shown:
        table.add_column(RECIPE_PARTS[i])

    table.add_column("owner", no_wrap=True)

    for name, languages, owner, parts in sorted(rows, key=lambda r: (r[0], r[2])):
        if parts is None:
            cells = [Text("no recipe", style=LABEL), *([""] * (len(shown) - 1))]
        else:
            cells = [parts[i] or "—" for i in shown]
        table.add_row(name, languages, *cells, owner)

    repl.console.print(table)


def _languages(held: list[tuple[str, ...]]) -> str:
    found = list(dict.fromkeys(lang for each in held for lang in each))
    return ", ".join(found) or "—"


def _alike(
    held: list[list[str | None] | None], title: Callable[[str | None], str]
) -> list[str | None] | None:
    if any(parts is None for parts in held):
        return None
    alike: list[str | None] = []
    for i in range(len(RECIPE_PARTS)):
        titles = {title(p[i]) for p in held if p and p[i]}
        alike.append(
            None if not titles else titles.pop() if len(titles) == 1 else "differs"
        )
    return alike


def _shown(rows: list[list[str | None] | None]) -> list[int]:
    return [
        i
        for i in range(len(RECIPE_PARTS))
        if any(parts and parts[i] is not None for parts in rows)
    ]


def _table(
    repl: Repl,
    rows: list[tuple[str, str, str, list[str | None] | None]],
    title: Callable[[str | None], str],
) -> None:
    shown = _shown([parts for _, _, _, parts in rows])
    table = Table(box=None, header_style="bold")

    for column in (
        "configuration",
        "languages",
        *(RECIPE_PARTS[i] for i in shown),
        "owner",
    ):
        table.add_column(column)

    for name, languages, owner, parts in sorted(rows, key=lambda r: (r[0], r[2])):
        if parts is None:
            cells = [Text("no recipe", style=LABEL), *([""] * (len(shown) - 1))]
        else:
            cells = [title(parts[i]) for i in shown]
        table.add_row(name, languages, *cells, owner)

    repl.console.print(table)


def endpoints(repl: Repl) -> None:
    bench = repl.bench
    table = Table(box=None, header_style="bold")

    for column in ("endpoint", "engine", "model", "url", "cleared for"):
        table.add_column(column)

    for name, spec in sorted(bench.inventory.endpoints.items()):
        cleared = " ".join(sorted(bench.inventory.cleared.get(name, ()))) or "—"
        try:
            found = bench.endpoint(name)
        except LookupError:
            said = Text(f"{short(spec.engine)}, not in the store", style=REFUSED)
            table.add_row(name, said, "", str(spec.url), cleared)
            continue
        table.add_row(
            name, bench.title(found.engine), found.model.name, str(spec.url), cleared
        )

    repl.console.print(table)


def cases(repl: Repl) -> None:
    families = repl.bench.families()
    repl.console.print(Text("  ".join(f.name for f in families)))
    tags = Counter(tag for f in families for tag in f.about.tags)
    tagged = ", ".join(f"{tag} {n}" for tag, n in sorted(tags.items()))
    said = plural(len(families), "case") + (f"; tagged {tagged}" if tagged else "")
    repl.console.print(said, style=LABEL)
