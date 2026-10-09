from rich.table import Table
from rich.text import Text

from chatddx.factors.select import reaches

from .render import LABEL, REFUSED, VALID
from .shell import Repl


def scorers(repl: Repl) -> None:
    bench, cell = repl.bench, repl.cell
    schema = None if cell.configuration is None else bench.skeleton(cell).output_schema
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
            if cell.configuration is None:
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
