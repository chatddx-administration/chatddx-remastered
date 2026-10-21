from difflib import SequenceMatcher

OPENING = "<<<<<<< signed"
DIVIDER = "======="
CLOSING = ">>>>>>> @stamp"
CONFLICT = ("<<<<<<<", ">>>>>>>")


def signed(text: str) -> list[str]:
    kept: list[str] = []
    opened: int | None = None
    divided = False
    for n, line in enumerate(text.splitlines(), 1):
        if opened is None and line == OPENING:
            opened = n
        elif opened is not None and not divided and line == DIVIDER:
            divided = True
        elif divided and line == CLOSING:
            opened, divided = None, False
        elif line.startswith(CONFLICT):
            raise ValueError(f"line {n}: a conflict marker that isn't a stamp's")
        elif not divided:
            kept.append(line)
    if opened is not None:
        raise ValueError(f"line {opened}: a stamp isn't closed")
    return kept


def stamps(text: str) -> list[tuple[str, ...]]:
    found: list[tuple[str, ...]] = []
    held: list[str] | None = None
    for line in text.splitlines():
        if held is None:
            held = [] if line == OPENING else None
        elif line == CLOSING:
            found.append(tuple(held))
            held = None
        else:
            held.append(line)
    return found


def _entries(lines: list[str]) -> int:
    return next(
        (i for i, line in enumerate(lines) if line.startswith("## ")), len(lines)
    )


def stamped(current: str | None, written: str) -> str:
    if current is None:
        return written
    old, new = signed(current), written.splitlines()
    lines = new[: _entries(new)]
    old, new = old[_entries(old) :], new[_entries(new) :]
    matched = SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matched.get_opcodes():
        if op == "equal":
            lines += old[i1:i2]
        else:
            lines += [OPENING, *old[i1:i2], DIVIDER, *new[j1:j2], CLOSING]
    return "\n".join(lines) + "\n"
