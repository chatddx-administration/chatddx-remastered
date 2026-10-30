import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Named:
    name: str
    line: int
    end: int
    column: int


@dataclass(frozen=True)
class Comment:
    line: int
    column: int
    text: str
    alone: bool

    @property
    def last(self) -> int:
        return self.line + self.text.count("\n")


@dataclass(frozen=True)
class Claim:
    line: int
    column: int
    end: int
    text: str


@dataclass(frozen=True)
class Entry:
    """A public name's entry in a surface, as its extractor renders it: the name it sorts
    by, its heading, and its lines below the heading."""

    name: str
    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class Facts:
    """What an extractor read off a file, whatever its language: the names it defines
    and the lines they span, its comments, and the statements a whoops index lists, with
    lines from 1 and columns from 0, for the index to anchor each to the name it is in or
    right above; and its surface's entries, as rendered."""

    path: str
    names: tuple[Named, ...]
    comments: tuple[Comment, ...]
    claims: tuple[Claim, ...]
    surface: tuple[Entry, ...] = ()


def dumped(facts: list[Facts]) -> str:
    return json.dumps([asdict(f) for f in facts], indent=2)


def loaded(text: str) -> list[Facts]:
    """Facts as dumped writes them, as an extractor in another language prints them."""
    return [
        Facts(
            held["path"],
            tuple(Named(**n) for n in held["names"]),
            tuple(Comment(**c) for c in held["comments"]),
            tuple(Claim(**c) for c in held["claims"]),
            tuple(
                Entry(e["name"], e["heading"], tuple(e["lines"]))
                for e in held["surface"]
            ),
        )
        for held in json.loads(text)
    ]
