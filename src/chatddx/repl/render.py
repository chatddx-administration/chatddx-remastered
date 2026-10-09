import json
from collections.abc import Iterable

from pydantic import JsonValue
from rich.text import Text

from chatddx.factors.base import Finding

LABEL = "dim"
REFUSED = "red"
VALID = "green"
LATER = "yellow"

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
