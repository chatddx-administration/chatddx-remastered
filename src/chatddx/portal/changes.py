import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

from pydantic import JsonValue

_TOKENS = re.compile(r"\s+|\w+|[^\w\s]")


@dataclass(frozen=True)
class Change:
    path: str
    was: Literal["added", "removed", "changed"]
    before: JsonValue = None
    after: JsonValue = None
    words: list[tuple[Literal["", "+", "-"], str]] | None = None


def changes(before: JsonValue, after: JsonValue, path: str = "") -> list[Change]:
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        found: list[Change] = []
        for key in [*after, *(k for k in before if k not in after)]:
            at = f"{path}/{key}"
            if key not in before:
                found.append(Change(at, "added", after=after[key]))
            elif key not in after:
                found.append(Change(at, "removed", before=before[key]))
            else:
                found += changes(before[key], after[key], at)
        return found
    if (
        isinstance(before, list)
        and isinstance(after, list)
        and len(before) == len(after)
    ):
        return [
            c
            for i, (b, a) in enumerate(zip(before, after, strict=True))
            for c in changes(b, a, f"{path}/{i}")
        ]
    words = (
        _words(before, after)
        if isinstance(before, str) and isinstance(after, str)
        else None
    )
    return [Change(path or "/", "changed", before, after, words)]


def _words(before: str, after: str) -> list[tuple[Literal["", "+", "-"], str]]:
    was, now = _TOKENS.findall(before), _TOKENS.findall(after)
    found: list[tuple[Literal["", "+", "-"], str]] = []
    matched = SequenceMatcher(None, was, now, autojunk=False)
    for op, i1, i2, j1, j2 in matched.get_opcodes():
        if op == "equal":
            found.append(("", "".join(was[i1:i2])))
            continue
        if i2 > i1:
            found.append(("-", "".join(was[i1:i2])))
        if j2 > j1:
            found.append(("+", "".join(now[j1:j2])))
    return found
