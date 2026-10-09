import json
import signal
from collections.abc import Generator
from contextlib import contextmanager
from types import FrameType
from typing import Any, Self

from pydantic import JsonValue
from rich.table import Table
from rich.text import Text

from chatddx.catalog.titles import short
from chatddx.factors.request import Skeleton
from chatddx.ledger import RunItem
from chatddx.runner.gate import Refused
from chatddx.runner.run import Event, ItemEnded, ItemStarted, Noted, Running, Streamed
from chatddx.runner.send import STOPPED
from chatddx.scorers.aggregate import mean, stderr
from chatddx.scorers.answer import Answer, read

from .bench import MAX_SEED, Cell, Graded, drawn_seed
from .render import (
    LABEL,
    LATER,
    REFUSED,
    TOKENS,
    VALID,
    Tally,
    Transcript,
    clipped_line,
    plural,
    usage,
    value_of,
)
from .shell import Repl


def seed(repl: Repl, value: str | None = None) -> None:
    if value is None:
        repl.seed = drawn_seed()
    elif (held := _seed_of(repl, value)) is None:
        return
    else:
        repl.seed = held

    repl.console.print(f"seed: #{repl.seed}")
    cell = repl.cell

    if cell.configuration is not None and repl.bench.skeleton(cell).greedy:
        repl.console.print("greedy: the seed isn't sent", style=LABEL)


def run(repl: Repl, name: str, seed: str | None = None) -> None:
    chosen = repl.seed if seed is None else _seed_of(repl, seed)
    cell = _whole(repl)

    if chosen is None or cell is None:
        return

    bench = repl.bench
    family = bench.family(name)
    skeleton = bench.skeleton(cell)
    running = _started(repl, cell, [family.case], chosen)

    if running is None:
        return

    title = f"trial: {cell.label} × {cell.endpoint} × {family.name} (seed {chosen})"
    repl.console.print(Text(title, style="bold"))
    transcript = Transcript(repl.console)
    ended: list[RunItem] = []

    def on_event(event: Event) -> None:
        transcript.event(event)
        if isinstance(event, ItemEnded):
            ended.append(event.item)

    try:
        running.send(on_event)
    except KeyboardInterrupt:
        transcript.begin(None)
        repl.console.print("(stopped)", style=LABEL)

    with _held():
        findings = running.finish()
        graded = bench.score(running.started)

    for item in ended:
        _said(repl, skeleton, item, graded)

    _scores(repl, graded)
    repl.say_findings(findings)
    trial = running.started.trial
    runs = [r for r in bench.reads.runs() if r.trial == trial]
    repl.console.print(
        f"recorded as run {len(runs)} of trial {short(trial)}, "
        + f"run {str(running.run)[:8]}",
        style=LABEL,
    )


def batch(repl: Repl, *tags: str) -> None:
    cell = _whole(repl)

    if cell is None:
        return

    bench = repl.bench
    families = bench.families(tags)
    tagged = " or ".join(tags)

    if not families:
        repl.error(f"no case tagged {tagged} for {bench.person.login}")
        return

    skeleton = bench.skeleton(cell)
    running = _started(repl, cell, [f.case for f in families], repl.seed)

    if running is None:
        return

    names = {f.case: f.name for f in families}
    width = max(len("case"), *(len(n) for n in names.values()))
    repl.console.print(
        Text(
            f"batch: {cell.label} × {cell.endpoint} × "
            + f"{plural(len(families), 'case')} tagged {tagged}, seed {repl.seed}",
            style="bold",
        )
    )
    header = f"{'case':<{width}}  {'tokens':>{TOKENS}}  outcome"
    repl.console.print(Text(header, style="bold"))
    ended: list[RunItem] = []
    noted: list[Noted] = []

    with _Stopping(running) as stopping:

        def on_event(event: Event) -> None:
            match event:
                case ItemStarted(key=key):
                    stopping.tally = Tally(repl.console, width, names[key.case])
                    _ = stopping.tally.__enter__()
                case Streamed(delta=delta) if stopping.tally is not None:
                    stopping.tally.count(delta.tokens)
                case ItemEnded(item=item) if stopping.tally is not None:
                    word, style, said = _outcome(skeleton, item)
                    stopping.tally.end(usage(item)[1], word, style, said)
                    stopping.tally.__exit__()
                    stopping.tally = None
                    ended.append(item)
                case Noted():
                    noted.append(event)
                case _:
                    pass

        try:
            running.send(on_event)
        except KeyboardInterrupt:
            pass
        finally:
            if stopping.tally is not None:
                stopping.tally.__exit__()

    with _held():
        findings = running.finish()
        graded = bench.score(running.started)

    if len(ended) < len(families):
        repl.console.print(
            f"stopped after {len(ended)} of {plural(len(families), 'case')}",
            style=LABEL,
        )

    repl.say_findings([n.finding for n in noted])
    _table(repl, names, ended, graded)
    _summary(repl, graded)
    repl.say_findings(findings)


def _seed_of(repl: Repl, value: str) -> int | None:
    if not (value.isascii() and value.isdigit()) or int(value) > MAX_SEED:
        repl.error(f"a seed is a whole number from 0 to {MAX_SEED}, not {value}")
        return None
    return int(value)


def _whole(repl: Repl) -> Cell | None:
    cell = repl.cell
    if cell.configuration is None or cell.endpoint is None:
        repl.error(
            "the cell needs a configuration and an endpoint: cell CONFIGURATION ENDPOINT"
        )
        return None
    return cell


def _started(repl: Repl, cell: Cell, cases: list[str], seed: int) -> Running | None:
    if repl.bench.skeleton(cell).greedy:
        repl.console.print("greedy: the seed isn't sent", style=LABEL)
    try:
        return repl.bench.start(cell, cases, seed)
    except Refused as e:
        repl.error(f"refused: {e}")
        return None


# How an item went: a word for it, its style, and what to say of it.
def _outcome(skeleton: Skeleton, item: RunItem) -> tuple[str, str, str | None]:
    last = item.calls[-1]
    answer = read(skeleton, last.response)
    if last.error == STOPPED:
        return "stopped", REFUSED, None
    if answer.value is None:
        if last.error is not None:
            return "errored", REFUSED, last.error
        return "unread", REFUSED, answer.problem
    if skeleton.output_schema is None:
        return "completed", "", last.error
    if answer.problem is not None:
        return "invalid", REFUSED, last.error or answer.problem
    return "valid", VALID, last.error


def _said(repl: Repl, skeleton: Skeleton, item: RunItem, graded: list[Graded]) -> None:
    last = item.calls[-1]
    answer = read(skeleton, last.response)

    if last.error is not None and last.error != STOPPED:
        repl.error(last.error)

    if answer.value is None:
        repl.error(f"unread: {answer.problem}")
        return

    if skeleton.output_schema is not None:
        if answer.problem is None:
            repl.console.print("valid", style=VALID)
        else:
            repl.error(f"invalid: {answer.problem}")

    _views(repl, answer, graded)


# What the scorers' views read from the answer, each selection once, but for those
# that read the answer whole.
def _views(repl: Repl, answer: Answer, graded: list[Graded]) -> None:
    seen: set[tuple[str, str | None]] = set()
    labels: set[str] = set()

    for g in graded:
        for i, view in enumerate(g.scorer.views):
            items = view.output_items(answer.value)
            if (view.output, view.split) in seen or items == [answer.value]:
                continue
            seen.add((view.output, view.split))
            label = g.label(i)
            shown = label if label not in labels else f"{label} ({g.name})"
            repl.console.print(shown, style="bold")
            labels.add(label)
            for n, picked in enumerate(items, 1):
                repl.console.print(Text(f"  {n}. {_shown(picked)}"))
            if not items:
                repl.console.print("  nothing", style=LABEL)


def _shown(value: JsonValue) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _detail(detail: JsonValue) -> Text:
    match detail:
        case None:
            return Text("")
        case {"reason": str() as reason}:
            return Text(reason, style=LABEL)
        case _:
            return Text(clipped_line(_shown(detail)))


def _scores(repl: Repl, graded: list[Graded]) -> None:
    if not graded:
        return

    repl.console.print("scores", style="bold")
    table = Table(box=None, show_header=False, padding=(0, 1, 0, 2))

    for g in graded:
        if g.score is None:
            table.add_row(g.name, "", "", Text(f"not scored: {g.refused}", LATER))
            continue
        for n, item in enumerate(g.score.items):
            table.add_row(
                g.name if n == 0 else "",
                g.label(item.view),
                value_of(item.value),
                _detail(item.detail),
            )

    repl.console.print(table)


def _table(
    repl: Repl, names: dict[str, str], ended: list[RunItem], graded: list[Graded]
) -> None:
    scored = [g for g in graded if g.score is not None]
    table = Table(box=None, header_style="bold")
    table.add_column("case")
    columns = [(g, i) for g in scored for i in range(len(g.scorer.views))]

    for g, i in columns:
        table.add_column(f"{g.name}\n{g.label(i)}")

    for item in ended:
        values: dict[tuple[int, str], float | None] = {}
        for g in scored:
            assert g.score is not None
            for s in g.score.items:
                if s.key == item.key:
                    values[(s.view, g.name)] = s.value
        table.add_row(
            names[item.key.case],
            *(value_of(values.get((i, g.name))) for g, i in columns),
        )

    if columns and ended:
        repl.console.print(table)

    for g in graded:
        if g.score is None:
            repl.console.print(Text(f"{g.name}: not scored: {g.refused}", LATER))


def _summary(repl: Repl, graded: list[Graded]) -> None:
    table = Table(box=None, header_style="bold")

    for column in ("scorer", "view", "scored", "mean", "stderr", "without a value"):
        table.add_column(column)

    rows = 0

    for g in graded:
        if g.score is None:
            continue
        for i in range(len(g.scorer.views)):
            items = [s for s in g.score.items if s.view == i]
            values = [s.value for s in items if s.value is not None]
            without = len(items) - len(values)
            table.add_row(
                g.name if i == 0 else "",
                g.label(i),
                str(len(values)),
                value_of(mean(values)) if values else "—",
                value_of(stderr(values)) if values else "—",
                str(without) if without else "",
            )
            rows += 1

    if rows:
        repl.console.print(table)


@contextmanager
def _held() -> Generator[None]:
    # While a run is written down and scored, a first Ctrl-C waits for it, and only a
    # second one goes through.
    pressed = 0

    def hold(_signal: int, _frame: FrameType | None) -> None:
        nonlocal pressed
        pressed += 1
        if pressed > 1:
            raise KeyboardInterrupt

    held = signal.signal(signal.SIGINT, hold)
    try:
        yield
    finally:
        _ = signal.signal(signal.SIGINT, held)


# In a batch, a first Ctrl-C lets the case under way finish and then stops, and a
# second stops that case too, which the runner records as stopped.
class _Stopping:
    def __init__(self, running: Running):
        self.running: Running = running
        self.pressed: int = 0
        self.tally: Tally | None = None
        self._held: Any = None

    def __enter__(self) -> Self:
        self._held = signal.signal(signal.SIGINT, self._pressed)
        return self

    def __exit__(self, *_exc: object) -> None:
        _ = signal.signal(signal.SIGINT, self._held)

    def _pressed(self, _signal: int, _frame: FrameType | None) -> None:
        self.pressed += 1
        if self.pressed > 1:
            raise KeyboardInterrupt
        self.running.stop()
        if self.tally is not None:
            self.tally.stopping()
