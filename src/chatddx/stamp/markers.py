from difflib import SequenceMatcher

_OPENING = "<<<<<<< signed"
_DIVIDER = "======="
# Policy: never spelled whole, so that a search for it finds the stamps pending alone.
_CLOSING = ">>>>>>> @" + "stamp"
_CONFLICT = ("<<<<<<<", ">>>>>>>")
PENDING = (
    f"- A stamp pending is a git conflict, from `{_OPENING}` to `{_DIVIDER}` as last "
    + "stamped and on to the `>>>>>>>` closing it as written now, till it is stamped."
)


def _sides(text: str) -> tuple[list[str], list[tuple[int, str]]]:
    kept: list[str] = []
    now: list[tuple[int, str]] = []
    opened: int | None = None
    divided = False
    for n, line in enumerate(text.splitlines(), 1):
        if opened is None and line == _OPENING:
            opened = n
        elif opened is not None and not divided and line == _DIVIDER:
            divided = True
        elif divided and line == _CLOSING:
            opened, divided = None, False
        elif line.startswith(_CONFLICT):
            raise ValueError(f"line {n}: a conflict marker that isn't a stamp's")
        else:
            if not divided:
                kept.append(line)
            if opened is None or divided:
                now.append((n, line))
    if opened is not None:
        raise ValueError(f"line {opened}: a stamp isn't closed")
    return kept, now


def signed(text: str) -> list[str]:
    return _sides(text)[0]


def applied(text: str) -> list[str]:
    return [line for _, line in _sides(text)[1]]


def applied_lines(text: str) -> list[tuple[int, str]]:
    return _sides(text)[1]


def stamps(text: str) -> list[tuple[str, ...]]:
    found: list[tuple[str, ...]] = []
    held: list[str] | None = None
    for line in text.splitlines():
        if held is None:
            held = [] if line == _OPENING else None
        elif line == _CLOSING:
            found.append(tuple(held))
            held = None
        else:
            held.append(line)
    return found


def _entries(lines: list[str]) -> int:
    fence = ""
    for i, line in enumerate(lines):
        if fence:
            fence = "" if line.startswith(fence) and not line.strip("`") else fence
        elif line.startswith("```"):
            fence = line[: len(line) - len(line.lstrip("`"))]
        elif line.startswith("## "):
            return i
    return len(lines)


def _marked(old: list[str], new: list[str]) -> list[str]:
    lines: list[str] = []
    matched = SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matched.get_opcodes():
        if op == "equal":
            lines += old[i1:i2]
        else:
            lines += [_OPENING, *old[i1:i2], _DIVIDER, *new[j1:j2], _CLOSING]
    return lines


def stamped(current: str | None, written: str) -> str:
    old, new = signed(current or ""), written.splitlines()
    lines = new[: _entries(new)] + _marked(old[_entries(old) :], new[_entries(new) :])
    return "\n".join(lines) + "\n"


def restamped(base: str | None, current: str) -> str:
    old = [] if base is None else signed(base)
    return "\n".join(_marked(old, applied(current))) + "\n"
