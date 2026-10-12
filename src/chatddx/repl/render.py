import json
from collections import Counter
from collections.abc import Iterable
from typing import Self

from pydantic import JsonValue
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from chatddx.bench import Bench, Graded, Outcome, outcome as ended, usage, used
from chatddx.catalog.titles import short
from chatddx.factors.base import Finding, resolve
from chatddx.factors.request import Skeleton, tool_calls
from chatddx.factors.scoring import Judge, Scorer, View
from chatddx.factors.select import select
from chatddx.ledger import Call, ItemKey, RunItem, ScoreItem
from chatddx.runner.run import Event, ItemEnded, Noted, Streamed, ToolRan
from chatddx.runner.score import (
    NO_EXPECTATION,
    Event as ScoringEvent,
    JudgeAnswered,
    JudgeAsked,
)
from chatddx.runner.send import STOPPED, Delta
from chatddx.scorers.aggregate import mean, stderr
from chatddx.scorers.answer import Answer, read
from chatddx.scorers.scorer import NO_ANSWER, NO_TARGET

LABEL = "dim"
REFUSED = "red"
VALID = "green"
LATER = "yellow"
THINKING = "#5f87af"

STYLES: dict[Outcome, str] = {
    "stopped": REFUSED,
    "errored": REFUSED,
    "unread": REFUSED,
    "completed": "",
    "invalid": REFUSED,
    "valid": VALID,
}

TOKENS = len("tokens")

# What the scoring pass notes of an answer, which show_answer says already.
ANSWERED = frozenset({"answer.unread", "answer.invalid"})

NAMED = 10

UNTARGETED: tuple[JsonValue, ...] = (NO_TARGET, NO_EXPECTATION)


def finding(f: Finding, times: int = 1) -> Text:
    return Text(
        f"[{f.level}] {f.code}: {f.message}" + (f" (×{times})" if times > 1 else ""),
        style=LATER if f.level == "warning" else LABEL,
    )


def counted(findings: Iterable[Finding]) -> list[tuple[Finding, int]]:
    first: dict[tuple[str, str, str], Finding] = {}
    times: Counter[tuple[str, str, str]] = Counter()
    for f in findings:
        said = (f.level, f.code, f.message)
        _ = first.setdefault(said, f)
        times[said] += 1
    return [(f, times[said]) for said, f in first.items()]


def scored_findings(graded: Iterable[Graded], read: bool = False) -> list[Finding]:
    found: dict[Finding, None] = {}
    for g in graded:
        if g.score is None:
            continue
        noted = () if g.score.finished is None else g.score.finished.findings
        for f in (*noted, *g.findings):
            if not (read and f.code in ANSWERED):
                found[f] = None
    return list(found)


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
                    used = f"{into} in, {out} out" if into else f"{out} out"
                    self.console.out(f"({used}{rounds})", style=LABEL, highlight=False)
            case Noted(finding=noted):
                self.begin(None)
                self.console.print(finding(noted))
            case _:
                pass

    def item(self, item: RunItem) -> None:
        self._message(item.call)
        for turn in item.turns:
            for ran in turn.tools:
                self.event(ToolRan(item.key, ran))
            if turn.call is not None:
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


class JudgeLines:
    def __init__(self, console: Console, bench: Bench) -> None:
        self.console: Console = console
        self.bench: Bench = bench
        self.asked: JudgeAsked | None = None
        self.tally: Tally | None = None

    def event(self, event: ScoringEvent) -> None:
        bench = self.bench
        match event:
            case JudgeAsked(key=key, scorer=scorer, view=view, judge=judge):
                self.close()
                seeds = len(resolve(bench.get, judge, Judge).seeds)
                label = bench.labels(scorer).get(view, f"view {view}")
                said = (
                    f"judging {bench.title(key.case)}: {label} by {bench.title(judge)}, "
                    + f"seed {event.seed_index + 1} of {seeds}"
                )
                self.asked = event
                self.tally = Tally(self.console, len(said), said).__enter__()
            case Streamed(delta=delta) if self.tally is not None:
                self.tally.count(delta.tokens)
            case JudgeAnswered(call=judged, verdict=verdict) if self.tally is not None:
                assert self.asked is not None
                scorer = resolve(bench.get, self.asked.scorer, Scorer)
                view = scorer.views[self.asked.view]
                said, _ = verdict_of(view, verdict)
                word, style = (said, "") if said is not None else ("unread", REFUSED)
                self.tally.end(used(judged.call)[1], word, style, judged.call.error)
                self.close()
            case _:
                pass

    def close(self) -> None:
        if self.tally is not None:
            self.tally.__exit__()
            self.tally = None


# `at` as the verdict metrics read it: src/chatddx/scorers/verdicts.py.
def verdict_of(view: View, verdict: JsonValue | None) -> tuple[str | None, str | None]:
    if verdict is None:
        return None, None
    at = view.params.get("at")
    if not isinstance(at, str) or not isinstance(verdict, dict):
        return clipped_line(_shown(verdict)), None
    picked = select(verdict, at)
    said = f"{at.rsplit('/', 1)[-1]} {_shown(picked[0]) if picked else '—'}"
    top = at.split("/")[1] if at.startswith("/") else None
    rest = [v for k, v in verdict.items() if k != top and isinstance(v, str)]
    return said, " ".join(rest) or None


def show_judged(console: Console, bench: Bench, graded: list[Graded]) -> None:
    table = Table(box=None, show_header=False, padding=(0, 1, 0, 2))

    for g in graded:
        if g.score is None:
            continue
        for item in g.score.items:
            view = g.scorer.views[item.view]
            for n, judged in enumerate(item.judge_calls):
                judge = resolve(bench.get, judged.judge, Judge)
                skeleton = resolve(bench.get, judge.skeleton, Skeleton)
                said, why = verdict_of(view, read(skeleton, judged.call.response).value)
                table.add_row(
                    g.label(item.view) if n == 0 else "",
                    f"{bench.title(judged.judge)}, seed {judged.seed_index + 1}",
                    said or Text("unread", style=REFUSED),
                    Text(judged.call.error, style=REFUSED)
                    if judged.call.error is not None
                    else (why or ""),
                )

    if table.row_count:
        console.print("judged", style="bold")
        console.print(table)


def outcome(skeleton: Skeleton, item: RunItem) -> tuple[str, str, str | None]:
    word, why = ended(skeleton, item)
    return word, STYLES[word], why


def show_answer(
    console: Console, skeleton: Skeleton, item: RunItem, graded: list[Graded]
) -> None:
    last = item.calls[-1]
    answer = read(skeleton, last.response)

    if last.error is not None:
        console.print(Text(last.error, style=REFUSED))

    if answer.value is None:
        if last.error != STOPPED:
            console.print(Text(f"unread: {answer.problem}", style=REFUSED))
        return

    if skeleton.output_schema is not None:
        if answer.problem is None:
            console.print("valid", style=VALID)
        else:
            console.print(Text(f"invalid: {answer.problem}", style=REFUSED))

    _views(console, answer, graded)


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
    untargeted: dict[str, list[str]] = {}

    for g in graded:
        if g.score is None:
            table.add_row(g.name, "", "", Text(f"not scored: {g.refused}", LATER))
            continue
        shown = False
        for item in g.score.items:
            if item.detail in UNTARGETED:
                untargeted.setdefault(g.name, []).append(g.label(item.view))
                continue
            table.add_row(
                g.name if not shown else "",
                g.label(item.view),
                value_of(item.value),
                _detail(item.detail),
            )
            shown = True

    if table.row_count:
        console.print(table)

    _untargeted(console, untargeted)


def show_table(
    console: Console, names: dict[str, str], items: list[RunItem], graded: list[Graded]
) -> None:
    scored = [g for g in graded if g.score is not None]
    held: dict[tuple[str, int, ItemKey], ScoreItem] = {}

    for g in scored:
        assert g.score is not None
        for s in g.score.items:
            held[(g.name, s.view, s.key)] = s

    columns: list[tuple[Graded, int]] = []
    untargeted: dict[str, list[str]] = {}

    for g in scored:
        for i in range(len(g.scorer.views)):
            found = [held.get((g.name, i, item.key)) for item in items]
            if found and all(s is not None and s.detail in UNTARGETED for s in found):
                untargeted.setdefault(g.name, []).append(g.label(i))
            else:
                columns.append((g, i))

    table = Table(box=None, header_style="bold")
    table.add_column("case")

    for g, i in columns:
        table.add_column(f"{g.name}\n{g.label(i)}")

    for item in items:
        values = [held.get((g.name, i, item.key)) for g, i in columns]
        table.add_row(
            names.get(item.key.case, short(item.key.case)),
            *(value_of(None if s is None else s.value) for s in values),
        )

    if columns and items:
        console.print(table)

    _untargeted(console, untargeted, " in any case")

    for g in graded:
        if g.score is None:
            console.print(Text(f"{g.name}: not scored: {g.refused}", LATER))


def _untargeted(console: Console, held: dict[str, list[str]], where: str = "") -> None:
    if held:
        said = "; ".join(f"{name} {', '.join(labels)}" for name, labels in held.items())
        console.print(Text(f"no target{where}: {said}", style=LABEL))


def show_summary(console: Console, graded: list[Graded]) -> None:
    held: dict[tuple[str, int], list[ScoreItem]] = {}
    labels: dict[tuple[str, int], str] = {}

    for g in graded:
        if g.score is None:
            continue
        for i in range(len(g.scorer.views)):
            _ = labels.setdefault((g.name, i), g.label(i))
            held.setdefault((g.name, i), []).extend(
                s for s in g.score.items if s.view == i
            )

    if not held:
        return

    table = Table(box=None, header_style="bold")
    columns = ("scorer", "view", "scored", "mean", "stderr")

    for column in (*columns, "no answer", "no target", "no value"):
        table.add_column(column)

    shown: set[str] = set()

    for (name, i), found in held.items():
        if not found:
            continue
        values = [s.value for s in found if s.value is not None]
        unvalued = [s.detail for s in found if s.value is None]
        unanswered = sum(d == NO_ANSWER for d in unvalued)
        untargeted = sum(d in UNTARGETED for d in unvalued)
        table.add_row(
            name if name not in shown else "",
            labels[(name, i)],
            str(len(values)),
            value_of(mean(values)) if values else "—",
            value_of(stderr(values)) if values else "—",
            *(
                str(n) if n else ""
                for n in (
                    unanswered,
                    untargeted,
                    len(unvalued) - unanswered - untargeted,
                )
            ),
        )
        shown.add(name)

    console.print(table)
