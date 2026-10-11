from collections.abc import Iterable

from rich.table import Table
from rich.text import Text

from chatddx.bench import Family, Graded
from chatddx.factors.select import reaches
from chatddx.ledger import RunStarted

from .render import (
    LABEL,
    LATER,
    REFUSED,
    VALID,
    plural,
    show_scores,
    show_summary,
    show_table,
    some,
)
from .reviewing import said
from .running import held
from .shell import Repl


# Scores the runs left to score, each under the scorers it has no score from as their
# scorings would be built now; with RUN, that run alone.
def score(repl: Repl, prefix: str | None = None) -> None:
    bench = repl.bench

    if prefix is None:
        outstanding = bench.outstanding()
        if not outstanding:
            repl.console.print("nothing to score", style=LABEL)
            return
        made: list[Graded] = []
        for started, unscored in outstanding:
            said(repl, started)
            with held():
                graded = bench.score(started, unscored)
            _scored(repl, started, graded)
            made += graded
        show_summary(repl.console, made)
        return

    started = bench.run(prefix)
    said(repl, started)

    if not bench.store.finished([started.run]):
        repl.console.print("unfinished: nothing to score", style=LABEL)
    elif unscored := bench.unscored(started):
        with held():
            graded = bench.score(started, unscored)
        _scored(repl, started, graded)
    elif not bench.scorers_for(started):
        repl.console.print("no scorer applies to it", style=LABEL)
    else:
        repl.console.print("scored already, as the scorings are now", style=LABEL)
        _scored(repl, started, bench.scores_of(started.run))


def _scored(repl: Repl, started: RunStarted, graded: list[Graded]) -> None:
    items = repl.bench.store.run(started.run).items
    if len(items) == 1:
        show_scores(repl.console, graded)
    else:
        names = {item.key.case: repl.bench.title(item.key.case) for item in items}
        show_table(repl.console, names, list(items), graded)


def scorers(repl: Repl) -> None:
    bench, variation = repl.bench, repl.cell.variation
    schema = None if variation is None else bench.skeleton(variation).output_schema
    table = Table(box=None, header_style="bold")

    for column in ("scorer", "view", "metric", "reads", "held to", "owner", "the cell"):
        table.add_column(column)

    for edit, about, scorer in bench.scorers():
        labels = bench.labels(edit.digest)
        name = about.name or bench.catalog.title(edit.thread)
        for i, view in enumerate(scorer.views):
            reads = view.output or "the whole answer"
            if view.split is not None:
                reads += f", {view.split}"
            metric = view.metric if view.judge is None else f"{view.metric}, judged"
            if variation is None:
                offered = Text("—", style=LABEL)
            elif reaches(schema, view.output):
                offered = Text("offers it", style=VALID)
            else:
                offered = Text("doesn't offer it", style=REFUSED)
            table.add_row(
                name if i == 0 else "",
                labels.get(i, f"view {i}"),
                metric,
                reads,
                view.expectation or "the whole expectation",
                bench.owner(about) if i == 0 else "",
                offered,
            )

    repl.console.print(table)


# Takes the expectations shared with the person for the cases with any TAG, all without,
# under each schema they are written in; `from OWNER` takes OWNER's only.
def take(repl: Repl, *words: str) -> None:
    if words[:1] == ("from",) and len(words) < 2:
        repl.error("usage: take [from OWNER] [TAG...]")
        return

    owner, tags = (words[1], words[2:]) if words[:1] == ("from",) else (None, words)

    bench = repl.bench
    families = bench.families(tags)
    tagged = f" tagged {' or '.join(tags)}" if tags else ""

    if not families:
        repl.error(f"no case{tagged} for {bench.person.login}")
        return

    under: dict[str, list[Family]] = {}

    for family in families:
        for schema in bench.expectation_schemas(family.case):
            under.setdefault(schema, []).append(family)

    if not under:
        repl.error(f"no expectation of a case{tagged} for {bench.person.login}")
        return

    for schema, picked in under.items():
        taken = bench.take([f.case for f in picked], schema, owner)
        names = {f.case: f.name for f in picked}
        by = f" from {owner}" if owner else ""
        repl.console.print(
            Text(
                f"take: {plural(len(picked), 'case')}{tagged}, under "
                + f"{bench.title(schema)}{by}",
                style="bold",
            )
        )
        table = Table(box=None, show_header=False)
        table.add_column(style=LABEL)
        table.add_column()
        table.add_row(
            "taken",
            Text(_some(names, taken.taken), style=VALID if taken.taken else LABEL),
        )
        if taken.kept:
            table.add_row("yours already", _some(names, taken.kept))
        if taken.choosing:
            choosing = (
                f"{names[case]} ({' '.join(sorted(_owners(repl, threads)))})"
                for case, threads in taken.choosing.items()
            )
            said = Text(some(choosing), style=LATER)
            _ = said.append(": take from OWNER", style=LABEL)
            table.add_row("to choose from", said)
        if taken.missing:
            table.add_row("none shared", _some(names, taken.missing))
        repl.console.print(table)


def _some(names: dict[str, str], cases: Iterable[str]) -> str:
    listed = sorted(names[c] for c in cases)
    return f"{len(listed)}: {some(listed)}" if listed else "none"


def _owners(repl: Repl, threads: Iterable[int]) -> set[str]:
    bench = repl.bench
    return {bench.login(bench.about(t).owner) for t in threads}
