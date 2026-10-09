from rich.table import Table
from rich.text import Text

from chatddx.bench import Graded
from chatddx.factors.select import reaches
from chatddx.ledger import RunStarted

from .render import LABEL, REFUSED, VALID, show_scores, show_summary, show_table
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
    elif not bench.reads.scorers(started):
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
