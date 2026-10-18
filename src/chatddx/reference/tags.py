import re
from difflib import SequenceMatcher

VERB = re.compile(r"^REFERENCE: (ADD|REPLACE|REMOVE)$")
FENCE = re.compile(r"^(`{3,})$")


def untagged(text: str) -> list[str]:
    lines = text.splitlines()
    kept: list[str] = []
    i = 0
    while i < len(lines):
        fence = FENCE.match(lines[i])
        if fence and i + 1 < len(lines) and VERB.match(lines[i + 1]):
            closing = [
                k for k in range(i + 2, len(lines)) if lines[k] == fence.group(1)
            ]
            if not closing:
                raise ValueError(f"line {i + 1}: a REFERENCE tag isn't closed")
            i = closing[0] + 1
            continue
        kept.append(lines[i])
        i += 1
    return kept


def pending(text: str) -> int:
    return sum(1 for line in text.splitlines() if VERB.match(line))


def _below(n: int) -> str:
    return "the line below" if n == 1 else f"the {n} lines below"


def _tag(verb: str, said: str, lines: list[str]) -> list[str]:
    longest = max((len(m.group(1)) for m in map(FENCE.match, lines) if m), default=2)
    fence = "`" * max(3, longest + 1)
    return [
        fence,
        f"REFERENCE: {verb}",
        said,
        *(["---", *lines] if lines else []),
        fence,
    ]


def tagged(current: str | None, written: str) -> str:
    if current is None:
        return written
    old, new = untagged(current), written.splitlines()
    lines: list[str] = []
    matched = SequenceMatcher(None, old, new, autojunk=False)
    for op, i1, i2, j1, j2 in matched.get_opcodes():
        if op == "insert":
            lines += _tag("ADD", "add these lines here", new[j1:j2])
        elif op == "delete":
            lines += _tag("REMOVE", f"remove {_below(i2 - i1)}", [])
        elif op == "replace":
            lines += _tag(
                "REPLACE", f"replace {_below(i2 - i1)} with these", new[j1:j2]
            )
        lines += old[i1:i2]
    return "\n".join(lines) + "\n"
