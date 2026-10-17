import signal
from types import FrameType
from typing import Any, Self

from rich.console import Console
from rich.text import Text

from chatddx.bench import Bench, Carried, Graded, Started, TriedVariation
from chatddx.catalog.titles import short
from chatddx.ledger import RunItem, RunStarted
from chatddx.runner.gate import Refused
from chatddx.runner.outcome import usage
from chatddx.runner.run import Event, ItemEnded, ItemStarted, Noted, Running, Streamed

from .render import (
    LABEL,
    LATER,
    TOKENS,
    JudgeLines,
    Tally,
    Transcript,
    outcome,
    plural,
    scored_findings,
    show_answer,
    show_judged,
    show_scores,
    show_summary,
    show_table,
)
from .shell import MAX_SEED, Repl, drawn_seed

WRITING = "the run is written down and scored first; Ctrl-C again stops the scoring"
SCORING = "Ctrl-C again stops the scoring"


def seed(repl: Repl, value: str | None = None) -> None:
    if value is None:
        repl.seed = drawn_seed()
    elif (held := _seed_of(repl, value)) is None:
        return
    else:
        repl.seed = held

    repl.console.print(f"seed: #{repl.seed}")
    variation = repl.cell.variation

    if variation is not None and repl.bench.skeleton(variation).greedy:
        repl.console.print("greedy: the seed isn't sent", style=LABEL)


def run(repl: Repl, name: str, seed: str | None = None) -> None:
    chosen = repl.seed if seed is None else _seed_of(repl, seed)
    whole = _whole(repl)

    if chosen is None or whole is None:
        return

    variation, endpoint = whole
    bench = repl.bench
    family, case = bench.case_titled(name)
    started = _started(repl, variation, endpoint, [case], chosen)

    if started is None:
        return

    carried, running = started.runs[0]
    skeleton = carried.skeleton
    assert skeleton is not None
    shown = family.name if case == family.case else bench.title(case)
    sent = _sent_in(carried, False)
    title = f"trial: {variation.label} × {endpoint} × {shown}{sent} (seed {chosen})"
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

    with Held(repl.console, WRITING) as held:
        findings = running.finish()
        graded = held.scored(bench, running.started)

    for item in ended:
        show_answer(repl.console, skeleton, item, graded)

    show_scores(repl.console, graded)
    show_judged(repl.console, bench, graded)
    repl.say_findings(scored_findings(graded, read=True))
    repl.say_findings(findings)
    held.said()
    _recorded(repl, running)


def tagged(repl: Repl, *tags: str) -> None:
    whole = _whole(repl)

    if whole is None:
        return

    variation, endpoint = whole
    bench = repl.bench
    families = bench.families(tags)
    any_of = " or ".join(tags)

    if not families:
        repl.error(f"no case tagged {any_of} for {bench.person.login}")
        return

    started = _started(repl, variation, endpoint, [f.case for f in families], repl.seed)

    if started is None:
        return

    names = {f.case: f.name for f in families}
    width = max(len("case"), *(len(n) for n in names.values()))
    stopped = False

    for carried, running in started.runs:
        tagged_as = f"tagged {any_of}{_sent_in(carried, len(started.runs) > 1)}"
        title = f"trial: {variation.label} × {endpoint} × "
        stopped = _tagged(
            repl, carried, running, names, width, stopped, title, tagged_as
        )

    for left in started.left_out:
        repl.console.print(
            f"left out: {plural(len(left.cases), 'case')} in {left.language}, "
            + f"as {left.refused}",
            style=LATER,
        )


def _sent_in(carried: Carried, several: bool) -> str:
    if carried.translated:
        return f", in {carried.language}, translated"
    if several and carried.language is not None:
        return f", in {carried.language}"
    return ""


def _tagged(
    repl: Repl,
    carried: Carried,
    running: Running,
    names: dict[str, str],
    width: int,
    stopped: bool,
    title: str,
    tagged_as: str,
) -> bool:
    bench = repl.bench
    skeleton = carried.skeleton
    assert skeleton is not None
    cases = len(carried.cases)
    repl.console.print(
        Text(
            f"{title}{plural(cases, 'case')} {tagged_as} (seed {repl.seed})",
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

        if stopped:
            running.stop()
        try:
            running.send(on_event)
        except KeyboardInterrupt:
            pass
        finally:
            if stopping.tally is not None:
                stopping.tally.__exit__()
        stopped = stopped or stopping.pressed > 0

    with Held(repl.console, WRITING) as held:
        findings = running.finish()
        graded = held.scored(bench, running.started)

    if len(ended) < cases:
        repl.console.print(
            f"stopped after {len(ended)} of {plural(cases, 'case')}", style=LABEL
        )

    repl.say_findings([n.finding for n in noted], tally=True)
    show_table(repl.console, names, ended, graded)
    show_summary(repl.console, graded)
    repl.say_findings([*scored_findings(graded), *findings], tally=True)
    held.said()
    _recorded(repl, running)
    return stopped


def _recorded(repl: Repl, running: Running) -> None:
    trial = running.started.trial
    runs = [r for r in repl.bench.runs() if r.trial == trial]
    repl.console.print(
        f"recorded as run {len(runs)} of trial {short(trial)}, "
        + f"run {str(running.run)[:8]}",
        style=LABEL,
    )


def case_and_seed(words: list[str]) -> list[str]:
    if "with" not in words[1:]:
        return words
    if words[-1].isdigit():
        return [" ".join(words[:-1]), words[-1]]
    return [" ".join(words)]


def _seed_of(repl: Repl, value: str) -> int | None:
    if not (value.isascii() and value.isdigit()) or int(value) > MAX_SEED:
        repl.error(f"a seed is a whole number from 0 to {MAX_SEED}, not {value}")
        return None
    return int(value)


def _whole(repl: Repl) -> tuple[TriedVariation, str] | None:
    cell = repl.cell
    if cell.variation is None:
        repl.error("the cell has no configuration: use CONFIGURATION")
        return None
    return cell.variation, repl.bench.at(cell.variation, cell.named).name


def _started(
    repl: Repl, variation: TriedVariation, endpoint: str, cases: list[str], seed: int
) -> Started | None:
    if repl.bench.skeleton(variation).greedy:
        repl.console.print("greedy: the seed isn't sent", style=LABEL)
    try:
        return repl.bench.start(variation, endpoint, cases, (seed,))
    except Refused as e:
        repl.error(f"refused: {e}")
        return None


class Held:
    def __init__(self, console: Console, said: str) -> None:
        self.console: Console = console
        self.message: str = said
        self.pressed: int = 0
        self.scoring: bool = False
        self._held: Any = None

    def __enter__(self) -> Self:
        self._held = signal.signal(signal.SIGINT, self._pressed)
        return self

    def __exit__(self, *_exc: object) -> None:
        _ = signal.signal(signal.SIGINT, self._held)

    @property
    def stopped(self) -> bool:
        return self.pressed > 1

    def scored(
        self, bench: Bench, run: RunStarted, scorers: list[str] | None = None
    ) -> list[Graded]:
        if self.stopped:
            return []
        self.scoring = True
        lines = JudgeLines(self.console, bench)
        try:
            return bench.score(run, scorers, lines.event)
        except KeyboardInterrupt:
            return []
        finally:
            lines.close()
            self.scoring = False

    def said(self) -> None:
        if self.stopped:
            self.console.print(
                "scoring stopped: score scores what is left", style=LATER
            )

    # A press goes through once, while scoring: the bench finishes the score under way.
    def _pressed(self, _signal: int, _frame: FrameType | None) -> None:
        self.pressed += 1
        if self.pressed == 1:
            self.console.print(self.message, style=LATER)
        elif self.pressed == 2 and self.scoring:
            raise KeyboardInterrupt


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
