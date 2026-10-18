import re
from difflib import SequenceMatcher

FENCE = re.compile(r"^(`{3,})$")


def _verb(tag: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(tag)}: (ADD|REPLACE|REMOVE)$")


def untagged(text: str, tag: str) -> list[str]:
    verb = _verb(tag)
    lines = text.splitlines()
    kept: list[str] = []
    i = 0
    while i < len(lines):
        fence = FENCE.match(lines[i])
        if fence and i + 1 < len(lines) and verb.match(lines[i + 1]):
            closing = [
                k for k in range(i + 2, len(lines)) if lines[k] == fence.group(1)
            ]
            if not closing:
                raise ValueError(f"line {i + 1}: a {tag} tag isn't closed")
            i = closing[0] + 1
            continue
        kept.append(lines[i])
        i += 1
    return kept


def pending(text: str, tag: str) -> int:
    verb = _verb(tag)
    return sum(1 for line in text.splitlines() if verb.match(line))


def _below(n: int) -> str:
    return "the line below" if n == 1 else f"the {n} lines below"


def _tag(tag: str, verb: str, said: str, lines: list[str]) -> list[str]:
    longest = max((len(m.group(1)) for m in map(FENCE.match, lines) if m), default=2)
    fence = "`" * max(3, longest + 1)
    return [
        fence,
        f"{tag}: {verb}",
        said,
        *(["---", *lines] if lines else []),
        fence,
    ]


def _entries(lines: list[str]) -> int:
    return next(
        (i for i, line in enumerate(lines) if line.startswith("## ")), len(lines)
    )


def tagged(current: str | None, written: str, tag: str) -> str:
    if current is None:
        return written
    old, new = untagged(current, tag), written.splitlines()
    lines = new[: _entries(new)]
    old, new = old[_entries(old) :], new[_entries(new) :]
    matched = SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matched.get_opcodes():
        if op == "insert":
            lines += _tag(tag, "ADD", "add these lines here", new[j1:j2])
        elif op == "delete":
            lines += _tag(tag, "REMOVE", f"remove {_below(i2 - i1)}", [])
        elif op == "replace":
            lines += _tag(
                tag, "REPLACE", f"replace {_below(i2 - i1)} with these", new[j1:j2]
            )
        lines += old[i1:i2]
    return "\n".join(lines) + "\n"
