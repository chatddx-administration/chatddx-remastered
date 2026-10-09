import signal
from collections.abc import Generator
from contextlib import contextmanager
from types import FrameType
from typing import Any, Self

from rich.text import Text

from chatddx.bench import MAX_SEED, Cell, drawn_seed
from chatddx.catalog.titles import short
from chatddx.ledger import RunItem
from chatddx.runner.gate import Refused
from chatddx.runner.run import Event, ItemEnded, ItemStarted, Noted, Running, Streamed

from .render import (
    LABEL,
    TOKENS,
    Tally,
    Transcript,
    outcome,
    plural,
    show_answer,
    show_scores,
    show_summary,
    show_table,
    usage,
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

    with held():
        findings = running.finish()
        graded = bench.score(running.started)

    for item in ended:
        show_answer(repl.console, skeleton, item, graded)

    show_scores(repl.console, graded)
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
                    word, style, said = outcome(skeleton, item)
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

    with held():
        findings = running.finish()
        graded = bench.score(running.started)

    if len(ended) < len(families):
        repl.console.print(
            f"stopped after {len(ended)} of {plural(len(families), 'case')}",
            style=LABEL,
        )

    repl.say_findings([n.finding for n in noted])
    show_table(repl.console, names, ended, graded)
    show_summary(repl.console, graded)
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


@contextmanager
def held() -> Generator[None]:
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
