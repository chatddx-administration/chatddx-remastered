import json
import re
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass

from pydantic import JsonValue

from chatddx.factors.base import Invalid

from .scorer import (
    NO_ANSWER,
    NO_TARGET,
    Explained,
    ExplainFunction,
    Mark,
    Metric,
    Scored,
    Verdicts,
    explaining,
)

_TOKEN = re.compile(r"\(|\)|&|\||[^\s&|()]+")
_WORD = re.compile(r"\w+")
_BREAK = re.compile(r"\n+|(?<=[.!?])\s+")


@dataclass(frozen=True)
class _Term:
    word: str
    stem: bool

    def fits(self, word: str) -> bool:
        return word.startswith(self.word) if self.stem else word == self.word


@dataclass(frozen=True)
class _Phrase:
    terms: tuple[_Term, ...]

    def example(self, _: Callable[[int], int]) -> list[str]:
        return [term.word for term in self.terms]

    def spans(self, words: list[str]) -> list[tuple[int, int]] | None:
        span = len(self.terms)
        for at in range(len(words) - span + 1):
            if all(term.fits(words[at + i]) for i, term in enumerate(self.terms)):
                return [(at, at + span)]
        return None


@dataclass(frozen=True)
class _All:
    parts: tuple["_Phrase | _All | _Any", ...]

    def example(self, pick: Callable[[int], int]) -> list[str]:
        return [word for part in self.parts for word in part.example(pick)]

    def spans(self, words: list[str]) -> list[tuple[int, int]] | None:
        found: list[tuple[int, int]] = []
        for part in self.parts:
            spans = part.spans(words)
            if spans is None:
                return None
            found += spans
        return sorted(found)


@dataclass(frozen=True)
class _Any:
    parts: tuple["_Phrase | _All | _Any", ...]

    def example(self, pick: Callable[[int], int]) -> list[str]:
        return self.parts[pick(len(self.parts))].example(pick)

    def spans(self, words: list[str]) -> list[tuple[int, int]] | None:
        found = [s for part in self.parts for s in part.spans(words) or ()]
        return sorted(found) if found else None


class Pattern:
    def __init__(self, text: str) -> None:
        self.text: str = text
        self._tokens: list[str] = _TOKEN.findall(text)
        self._at: int = 0
        if not self._tokens:
            raise Invalid.of("a pattern names at least one word")
        self._root: _Phrase | _All | _Any = self._any()
        if self._peek() is not None:
            raise Invalid.of(
                "unexpected %(token)s in %(text)s",
                token=repr(self._peek()),
                text=repr(text),
            )

    def example(self, pick: Callable[[int], int]) -> str:
        """A text the pattern finds, with `pick(n)` choosing among n alternatives."""
        return " ".join(self._root.example(pick))

    def alternatives(self) -> list[str]:
        """Each alternative of the pattern's at its top level, as a pattern of its own:
        what finds a text the pattern finds, joined by `|`."""
        found: list[list[str]] = [[]]
        depth = 0
        for token in self._tokens:
            if token == "|" and depth == 0:
                found.append([])
                continue
            depth += (token == "(") - (token == ")")
            found[-1].append(token)
        return [
            " ".join(tokens).replace("( ", "(").replace(" )", ")") for tokens in found
        ]

    def find(self, text: str) -> int | None:
        found = self.spans(text)
        return None if found is None else found[0][0]

    def spans(self, text: str) -> list[tuple[int, int]] | None:
        words = list(_WORD.finditer(text))
        found = self._root.spans([word.group().casefold() for word in words])
        if found is None:
            return None
        return [(words[at].start(), words[end - 1].end()) for at, end in found]

    def _peek(self) -> str | None:
        return self._tokens[self._at] if self._at < len(self._tokens) else None

    def _take(self) -> str | None:
        token = self._peek()
        self._at += 1
        return token

    def _any(self) -> "_Phrase | _All | _Any":
        parts = [self._all()]
        while self._peek() == "|":
            _ = self._take()
            parts.append(self._all())
        return parts[0] if len(parts) == 1 else _Any(tuple(parts))

    def _all(self) -> "_Phrase | _All | _Any":
        parts = [self._one()]
        while self._peek() == "&":
            _ = self._take()
            parts.append(self._one())
        return parts[0] if len(parts) == 1 else _All(tuple(parts))

    def _one(self) -> "_Phrase | _All | _Any":
        if self._peek() == "(":
            _ = self._take()
            inner = self._any()
            if self._take() != ")":
                raise Invalid.of(
                    "a '(' in %(text)s is never closed", text=repr(self.text)
                )
            return inner
        terms: list[_Term] = []
        while (token := self._peek()) not in (None, "&", "|", "(", ")"):
            _ = self._take()
            terms += _terms(token)
        if not terms:
            raise Invalid.of("a word is missing in %(text)s", text=repr(self.text))
        return _Phrase(tuple(terms))


def _terms(token: str) -> list[_Term]:
    stem = token.endswith("*")
    words = [word.casefold() for word in _WORD.findall(token)]
    if not words:
        raise Invalid.of("%(token)s names no word", token=repr(token))
    return [_Term(word, stem and i == len(words) - 1) for i, word in enumerate(words)]


def _units(text: str) -> Iterator[tuple[int, str]]:
    start = 0
    for gap in _BREAK.finditer(text):
        yield start, text[start : gap.start()]
        start = gap.end()
    yield start, text[start:]


def reciprocal_rank(items: list[str] | None, target: str) -> Scored:
    return _ranked(items, target).scored


def first_mention(items: list[str] | None, target: str) -> Scored:
    return _first(items, target).scored


def mentions(items: list[str] | None, target: str | None) -> Scored:
    return _mentioned(items, target).scored


def _marked(item: int, spans: list[tuple[int, int]], by: int = 0) -> tuple[Mark, ...]:
    return tuple(Mark(item, by + start, by + end) for start, end in spans)


def _ranked(items: list[str] | None, target: str) -> Explained:
    if items is None:
        return Explained(Scored(None, NO_ANSWER))
    pattern = Pattern(target)
    for rank, item in enumerate(items, 1):
        if (spans := pattern.spans(item)) is not None:
            scored = Scored(1 / rank, {"answer": f"{rank}. {item}"})
            return Explained(scored, items, _marked(rank - 1, spans))
    return Explained(Scored(0.0, {"reason": "not listed"}), items)


def _first(items: list[str] | None, target: str) -> Explained:
    if items is None:
        return Explained(Scored(None, NO_ANSWER))
    pattern = Pattern(target)
    for i, item in enumerate(items):
        for start, unit in _units(item):
            if (spans := pattern.spans(unit)) is not None:
                scored = Scored(float(start + spans[0][0]), {"answer": unit.strip()})
                return Explained(scored, items, _marked(i, spans, start))
    return Explained(Scored(None, {"reason": "never named"}), items)


def _mentioned(items: list[str] | None, target: str | None) -> Explained:
    if items is None:
        return Explained(Scored(None, NO_ANSWER))
    if target is None:
        if items:
            scored = Scored(0.0, {"answer": items[0], "reason": "none expected"})
            return Explained(scored, items, (Mark(0, 0, len(items[0])),))
        return Explained(Scored(1.0, {"reason": "none named, as expected"}), items)
    pattern = Pattern(target)
    for i, item in enumerate(items):
        if (spans := pattern.spans(item)) is not None:
            return Explained(Scored(1.0, {"answer": item}), items, _marked(i, spans))
    return Explained(Scored(0.0, {"reason": "not named"}), items)


def _texts(output: list[JsonValue] | None) -> list[str] | None:
    if output is None:
        return None
    return [
        item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        for item in output
        if item is not None
    ]


def _target(expected: list[JsonValue]) -> str | None | Scored:
    found = _written(expected)
    if isinstance(found, str) and (refused := _unreadable(found)) is not None:
        return Scored(None, {"reason": f"the pattern doesn't read: {refused}"})
    return found


def _refused(expected: list[JsonValue]) -> Invalid | None:
    found = _written(expected)
    return _unreadable(found) if isinstance(found, str) else None


def _unreadable(text: str) -> Invalid | None:
    try:
        _ = Pattern(text)
    except Invalid as e:
        return e
    return None


def _written(expected: list[JsonValue]) -> str | None | Scored:
    if not expected:
        return Scored(None, NO_TARGET)
    if len(expected) > 1:
        return Scored(None, {"reason": f"{len(expected)} targets, not one"})
    match expected[0]:
        case False:
            return None
        case str() as pattern:
            text = pattern
        case {"pattern": str() as pattern}:
            text = pattern
        case {"text": str()}:
            return Scored(
                None, {"reason": "the target has words, for a judge, but no pattern"}
            )
        case _:
            return Scored(None, {"reason": "the target has no pattern"})
    return text


def _by_pattern(find: Callable[[list[str] | None, str], Explained]) -> ExplainFunction:
    def metric(
        output: list[JsonValue] | None,
        expected: list[JsonValue],
        _params: Mapping[str, JsonValue],
        _verdicts: Verdicts | None,
    ) -> Explained:
        target = _target(expected)
        if isinstance(target, Scored):
            return Explained(target)
        if target is None:
            return Explained(
                Scored(None, {"reason": "nothing is expected to be found"})
            )
        return find(_texts(output), target)

    return metric


def _mentions(
    output: list[JsonValue] | None,
    expected: list[JsonValue],
    _params: Mapping[str, JsonValue],
    _verdicts: Verdicts | None,
) -> Explained:
    target = _target(expected)
    if isinstance(target, Scored):
        return Explained(target)
    return _mentioned(_texts(output), target)


METRICS: dict[str, Metric] = {
    "reciprocal_rank": explaining(
        "1 over the rank of the first item that matches the target's pattern; 0 "
        + "when none does, and none without an answer",
        _by_pattern(_ranked),
        reads=_target,
        refuses=_refused,
    ),
    "first_mention": explaining(
        "where in the text the target's pattern is first matched, in characters; "
        + "none when it never is",
        _by_pattern(_first),
        unit="@",
        reads=_target,
        refuses=_refused,
    ),
    "mentions": explaining(
        "1 when an item matches the target's pattern, or when nothing is named "
        + "and nothing is expected; else 0, and none without an answer",
        _mentions,
        reads=_target,
        refuses=_refused,
    ),
}
