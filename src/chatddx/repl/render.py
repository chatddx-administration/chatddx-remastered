import json
from collections.abc import Iterable
from typing import Self

from pydantic import JsonValue
from rich.console import Console
from rich.live import Live
from rich.text import Text

from chatddx.factors.base import Finding
from chatddx.ledger import RunItem
from chatddx.runner.run import Event, ItemEnded, Noted, Streamed, ToolRan
from chatddx.runner.send import Delta

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
