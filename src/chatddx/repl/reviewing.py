from collections import Counter

from rich.table import Table
from rich.text import Text

from chatddx.bench import Graded
from chatddx.catalog.titles import short
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.ledger import Run, RunItem, RunStarted
from chatddx.runner import rendered_again, usage
from chatddx.scorers.aggregate import mean
from chatddx.scorers.shipped import unit_of

from .render import (
    LABEL,
    LATER,
    REFUSED,
    TOKENS,
    Transcript,
    clipped_line,
    outcome,
    scored_findings,
    show_answer,
    show_judged,
    show_scores,
    show_summary,
    show_table,
    value_of,
)
from .shell import Repl


def runs(repl: Repl, count: str = "20") -> None:
    if not (count.isascii() and count.isdigit()):
        repl.error(f"a count is a whole number, not {count}")
        return

    bench = repl.bench
    found = bench.runs()[: int(count)]

    if not found:
        repl.console.print(f"{bench.person.login} has no runs", style=LABEL)
        return

    table = Table(box=None, header_style="bold")

    for column in ("run", "when", "trial", "what ran", "outcome", "scores"):
        table.add_column(column)

    for started in found:
        run = bench.store.run(started.run)
        graded = bench.scores_of(started)
        table.add_row(
            str(started.run)[:8],
            when(started),
            short(started.trial),
            bench.described(started),
            _outcomes(repl, run),
            "\n".join(_means(g) for g in graded),
        )

    repl.console.print(table)


def replay(repl: Repl, prefix: str | None = None) -> None:
    bench = repl.bench
    started = bench.run(prefix)
    run = bench.store.run(started.run)
    said(repl, started)
    rig = started.rig
    at = "" if started.endpoint is None else f"at {started.endpoint.url}, "
    built = f"{rig.distribution} {rig.version}" + (
        f" at {rig.revision}" if rig.revision else ""
    )
    stage = "finished" if run.finished is not None else "unfinished"
    repl.console.print(f"{when(started)}, {stage}, {at}on {built}", style=LABEL)

    again = rendered_again(bench.conn, bench.inventory, run)
    differ = {key: why for key, why in again.items() if why is not None}

    if not differ:
        repl.console.print(
            "the request, rendered again from the trial and the source, is the one "
            + "that was sent",
            style=LABEL,
        )

    for key, why in differ.items():
        repl.console.print(
            Text(
                f"{bench.title(key.case)}: rendered again, the request differs: {why}",
                style=REFUSED,
            )
        )

    skeleton = _skeleton(repl, started)
    graded = bench.scores_of(started)

    if len(run.items) == 1:
        [item] = run.items
        Transcript(repl.console).item(item)
        show_answer(repl.console, skeleton, item, graded)
        show_scores(repl.console, graded)
        show_judged(repl.console, repl.bench, graded)
        repl.say_findings(scored_findings(graded, read=True))
        return

    _lines(repl, skeleton, run.items)
    names = {item.key.case: bench.title(item.key.case) for item in run.items}
    show_table(repl.console, names, list(run.items), graded)
    show_summary(repl.console, graded)
    repl.say_findings(scored_findings(graded), tally=True)


def said(repl: Repl, started: RunStarted) -> None:
    trial = short(started.trial)
    what = repl.bench.described(started)
    repl.console.print(
        Text(f"run {str(started.run)[:8]} of trial {trial}: {what}", style="bold")
    )


def when(started: RunStarted) -> str:
    return started.at.astimezone().strftime("%Y-%m-%d %H:%M")


def _skeleton(repl: Repl, started: RunStarted) -> Skeleton:
    trial = resolve(repl.bench.store.get, started.trial, Trial)
    return resolve(repl.bench.store.get, trial.skeleton, Skeleton)


def _lines(repl: Repl, skeleton: Skeleton, items: tuple[RunItem, ...]) -> None:
    names = {item.key.case: repl.bench.title(item.key.case) for item in items}
    width = max(len("case"), *(len(n) for n in names.values()))
    header = f"{'case':<{width}}  {'tokens':>{TOKENS}}  outcome"
    repl.console.print(Text(header, style="bold"))

    for item in sorted(items, key=lambda i: (names[i.key.case], i.key.replicate)):
        word, style, why = outcome(skeleton, item)
        line = Text(f"{names[item.key.case]:<{width}}  {usage(item)[1]:>{TOKENS}}")
        _ = line.append(f"  {word}", style=style)
        if why is not None:
            _ = line.append(f"  {clipped_line(why)}", style=REFUSED)
        repl.console.print(line)


def _outcomes(repl: Repl, run: Run) -> Text:
    skeleton = _skeleton(repl, run.started)
    words = [outcome(skeleton, item) for item in run.items]
    text = Text()

    if len(words) == 1:
        [(word, style, why)] = words
        _ = text.append(word, style=style)
        if why is not None:
            _ = text.append(f": {clipped_line(why, 40)}", style=REFUSED)
    elif words:
        counted = Counter(word for word, _, _ in words)
        _ = text.append(", ".join(f"{n} {word}" for word, n in counted.items()))

    if run.finished is None:
        _ = text.append(", unfinished" if words else "unfinished", style=LATER)

    return text


def _means(graded: Graded) -> str:
    assert graded.score is not None
    means: list[str] = []
    for i in range(len(graded.scorer.views)):
        values = [
            s.value for s in graded.score.items if s.view == i and s.value is not None
        ]
        means.append(
            value_of(mean(values), unit_of(graded.scorer, i)) if values else "—"
        )
    return f"{graded.name} {'/'.join(means)}"
