import json
from collections.abc import Iterable
from typing import Self

from pydantic import JsonValue
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from chatddx.catalog.titles import short
from chatddx.factors.base import Finding
from chatddx.factors.request import Skeleton, tool_calls
from chatddx.ledger import Call, RunItem
from chatddx.runner.run import Event, ItemEnded, Noted, Streamed, ToolRan
from chatddx.runner.send import STOPPED, Delta
from chatddx.scorers.aggregate import mean, stderr
from chatddx.scorers.answer import Answer, read

from .bench import Graded

LABEL = "dim"
REFUSED = "red"
VALID = "green"
LATER = "yellow"
THINKING = "#5f87af"

TOKENS = len("tokens")

NAMED = 10


def finding(f: Finding) -> Text:
    return Text(
        f"[{f.level}] {f.code}: {f.message}",
        style=LATER if f.level == "warning" else LABEL,
    )


def writes(values: dict[str, JsonValue], prefix: str = "") -> str:
    fields: list[str] = []
    for key, value in values.items():
        if isinstance(value, dict):
            fields.append(writes(value, f"{prefix}{key}."))
        else:
            fields.append(f"{prefix}{key}={json.dumps(value, ensure_ascii=False)}")
    return " ".join(field for field in fields if field)


def some(names: Iterable[str]) -> str:
    listed = list(names)
    more = len(listed) - NAMED
    return " ".join(listed[:NAMED]) + (f" and {more} more" if more > 0 else "")


def clipped(text: str, lines: int = 30) -> str:
    kept = text.splitlines()
    if len(kept) <= lines:
        return text
    return "\n".join(kept[:lines]) + f"\n… {len(kept) - lines} more lines"


def plural(n: int, one: str, many: str | None = None) -> str:
    return f"{n} {one if n == 1 else many or one + 's'}"


def value_of(value: float | None) -> str:
    if value is None:
        return "—"
    return str(int(value)) if value.is_integer() else f"{value:.3g}"


def clipped_line(text: str, width: int = 60) -> str:
    line = text.splitlines()[0] if text else ""
    return line if len(line) <= width else line[: width - 1] + "…"


def usage(item: RunItem) -> tuple[int, int]:
    used = [
        u
        for call in item.calls
        if call.response is not None
        and isinstance(u := call.response.get("usage"), dict)
    ]
    return (
        sum(n for u in used if isinstance(n := u.get("prompt_tokens"), int)),
        sum(n for u in used if isinstance(n := u.get("completion_tokens"), int)),
    )


# A run's events as they stream: the thinking, labelled, then the answer, each tool
# call labelled by its name and followed by what it returned, and the tokens used.
class Transcript:
    def __init__(self, console: Console):
        self.console: Console = console
        self.at_start: bool = True
        self.labelled: bool = False
        self.held: str = ""
        self.kind: str | None = None

    def event(self, event: Event) -> None:
        match event:
            case Streamed(delta=Delta(kind=kind, text=text)) if kind != self.kind:
                # A call's name comes first, and its arguments after it.
                self.begin({"reasoning": "thinking", "content": None}.get(kind, text))
                self.kind = kind
                if kind != "tool_call":
                    self.write(text, THINKING if kind == "reasoning" else "")
            case Streamed(delta=Delta(kind=kind, text=text)):
                self.write(text, THINKING if kind == "reasoning" else "")
            case ToolRan(run=ran):
                self.begin("result")
                self.write(ran.result if ran.error is None else f"error: {ran.error}")
                self.begin(None)
            case ItemEnded(item=item):
                self.begin(None)
                into, out = usage(item)
                calls = len(item.calls)
                rounds = f", {calls} requests" if calls > 1 else ""
                if into or out:
                    self.console.out(
                        f"({into} in, {out} out{rounds})", style=LABEL, highlight=False
                    )
            case Noted(finding=noted):
                self.begin(None)
                self.console.print(finding(noted))
            case _:
                pass

    # A stored item told again as it streamed: each call's message, and the results of
    # the tools it called before the next.
    def item(self, item: RunItem) -> None:
        self._message(item.call)
        for turn in item.turns:
            for ran in turn.tools:
                self.event(ToolRan(item.key, ran))
            self._message(turn.call)
        self.event(ItemEnded(item))

    def _message(self, call: Call) -> None:
        response = call.response or {}
        match response.get("choices"):
            case [{"message": dict() as message}, *_]:
                pass
            case _:
                message = {}
        reasoning = message.get("reasoning") or message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning.strip():
            self.begin("thinking")
            self.write(reasoning.rstrip(), THINKING)
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            self.begin(None)
            self.write(content.rstrip())
        for called in tool_calls(response):
            self.begin(called.name)
            self.write(called.arguments)

    def write(self, text: str, style: str = "") -> None:
        if self.labelled:
            text = text.lstrip()
        if text.isspace():
            self.held += text
        elif text:
            self._out(self.held + text, style)

    # What a part ends with that is only whitespace is left out, as a model that runs
    # away writes nothing else.
    def begin(self, label: str | None) -> None:
        self.kind = None
        self.held = ""
        if not self.at_start:
            self.console.out("")
            self.at_start = True
        self.labelled = False
        if label:
            self.console.out(f"[{label}] ", style=LABEL, end="", highlight=False)
            self.at_start = False
            self.labelled = True

    def _out(self, text: str, style: str = "") -> None:
        self.console.out(text, style=style or None, end="", highlight=False)
        self.held = ""
        self.at_start = text.endswith("\n")
        self.labelled = False


# A batch's line for one case: the tokens climb while it runs, and then it says how it
# went.
class Tally:
    def __init__(self, console: Console, width: int, case: str):
        self.console: Console = console
        self.width: int = width
        self.case: str = case
        self.tokens: int = 0
        self.counted: bool = False
        self.last: bool = False
        self.live: Live = Live(self._line(), console=console, auto_refresh=False)

    def __enter__(self) -> Self:
        self.live.start(refresh=True)
        return self

    def __exit__(self, *_: object) -> None:
        if self.last:
            self.last = False
            self.live.update(self._line())
        self.live.stop()
        if not self.console.is_terminal:
            self.console.line()

    def count(self, tokens: int) -> None:
        self.tokens = tokens
        self.live.update(self._line(), refresh=True)

    def stopping(self) -> None:
        self.last = True
        self.live.update(self._line(), refresh=True)

    def end(self, tokens: int, word: str, style: str, said: str | None) -> None:
        self.tokens, self.counted, self.last = tokens, True, False
        line = self._line()
        _ = line.append(f"  {word}", style=style)
        if said is not None:
            _ = line.append(f"  {clipped_line(said)}", style=REFUSED)
        self.live.update(line, refresh=True)

    def _line(self) -> Text:
        tokens = str(self.tokens) if self.counted else f"~{self.tokens}"
        line = Text(f"{self.case:<{self.width}}  {tokens:>{TOKENS}}")
        if self.last:
            _ = line.append(
                "  stopping after this case (Ctrl-C again stops it now)", LATER
            )
        return line


# How an item went: a word for it, its style, and what to say of it.
def outcome(skeleton: Skeleton, item: RunItem) -> tuple[str, str, str | None]:
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


# An item's answer as the scorers read it: the call's error, whether the answer holds to
# the output's schema, and what the views pick from it.
def show_answer(
    console: Console, skeleton: Skeleton, item: RunItem, graded: list[Graded]
) -> None:
    last = item.calls[-1]
    answer = read(skeleton, last.response)

    if last.error is not None and last.error != STOPPED:
        console.print(Text(last.error, style=REFUSED))

    if answer.value is None:
        console.print(Text(f"unread: {answer.problem}", style=REFUSED))
        return

    if skeleton.output_schema is not None:
        if answer.problem is None:
            console.print("valid", style=VALID)
        else:
            console.print(Text(f"invalid: {answer.problem}", style=REFUSED))

    _views(console, answer, graded)


# What the scorers' views read from the answer, each selection once, but for those
# that read the answer whole.
def _views(console: Console, answer: Answer, graded: list[Graded]) -> None:
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
            console.print(shown, style="bold")
            labels.add(label)
            for n, picked in enumerate(items, 1):
                console.print(Text(f"  {n}. {_shown(picked)}"))
            if not items:
                console.print("  nothing", style=LABEL)


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


def show_scores(console: Console, graded: list[Graded]) -> None:
    if not graded:
        return

    console.print("scores", style="bold")
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

    console.print(table)


# Each item's value per scorer view, an item to a row.
def show_table(
    console: Console, names: dict[str, str], items: list[RunItem], graded: list[Graded]
) -> None:
    scored = [g for g in graded if g.score is not None]
    table = Table(box=None, header_style="bold")
    table.add_column("case")
    columns = [(g, i) for g in scored for i in range(len(g.scorer.views))]

    for g, i in columns:
        table.add_column(f"{g.name}\n{g.label(i)}")

    for item in items:
        values: dict[tuple[int, str], float | None] = {}
        for g in scored:
            assert g.score is not None
            for s in g.score.items:
                if s.key == item.key:
                    values[(s.view, g.name)] = s.value
        table.add_row(
            names.get(item.key.case, short(item.key.case)),
            *(value_of(values.get((i, g.name))) for g, i in columns),
        )

    if columns and items:
        console.print(table)

    for g in graded:
        if g.score is None:
            console.print(Text(f"{g.name}: not scored: {g.refused}", LATER))


# Per scorer view, over every score given: how many items have a value, their mean and
# standard error, and how many have none.
def show_summary(console: Console, graded: list[Graded]) -> None:
    held: dict[tuple[str, int], list[float | None]] = {}
    labels: dict[tuple[str, int], str] = {}

    for g in graded:
        if g.score is None:
            continue
        for i in range(len(g.scorer.views)):
            _ = labels.setdefault((g.name, i), g.label(i))
            held.setdefault((g.name, i), []).extend(
                s.value for s in g.score.items if s.view == i
            )

    if not held:
        return

    table = Table(box=None, header_style="bold")

    for column in ("scorer", "view", "scored", "mean", "stderr", "without a value"):
        table.add_column(column)

    shown: set[str] = set()

    for (name, i), found in held.items():
        values = [v for v in found if v is not None]
        without = len(found) - len(values)
        table.add_row(
            name if name not in shown else "",
            labels[(name, i)],
            str(len(values)),
            value_of(mean(values)) if values else "—",
            value_of(stderr(values)) if values else "—",
            str(without) if without else "",
        )
        shown.add(name)

    console.print(table)
