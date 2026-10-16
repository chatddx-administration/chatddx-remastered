from dataclasses import dataclass, field
from typing import Literal

from chatddx.catalog import About, Behind, Divergence, Edit, Kept, Part
from chatddx.factors.base import Component, Finding
from chatddx.factors.request import CHUNK_PARTS, Recipe, Skeleton, SlotName
from chatddx.factors.scoring import Scorer
from chatddx.ledger import Score
from chatddx.runner.run import Running

from .variation import TriedVariation

KINDS: dict[str, tuple[str, ...]] = {
    "configuration": ("skeleton",),
    **{part: (f"chunk.{part}",) for part in CHUNK_PARTS},
    "tool": ("tool",),
    "scorer": ("scorer",),
    "judge": ("judge",),
    "expectation_schema": ("expectation_schema",),
    "expectation": ("expectation",),
    "appendix": ("appendix",),
    "canary_set": ("canary_set",),
    "model": ("model",),
    "engine": ("engine.local", "engine.remote"),
    "facts": ("facts",),
}


def word_of(kind: str) -> str:
    return next(w for w, held in KINDS.items() if kind in held)


WRITTEN: frozenset[str] = frozenset(
    {
        *(f"chunk.{part}" for part in CHUNK_PARTS),
        "expectation",
        "appendix",
        "scorer",
        "judge",
    }
)

LABELLED: tuple[Part, ...] = ("view", "resource")

COMPILED_LANGUAGE = "a compiled configuration's language comes from its recipe"

PLACEHOLDERS: dict[SlotName, str] = {
    "vignette": "‹vignette›",
    "appendices": "‹appendices›",
    "completion": "‹completion›",
    "expectation": "‹expectation›",
}


@dataclass(frozen=True)
class Family:
    id: int
    about: About
    case: str

    @property
    def name(self) -> str:
        return self.about.name or f"family {self.id}"


@dataclass(frozen=True)
class Carried:
    language: str | None
    cases: list[str]
    skeleton: Skeleton | None = None
    translated: bool = False
    refused: str | None = None


@dataclass(frozen=True)
class Started:
    runs: list[tuple[Carried, Running]]
    left_out: list[Carried]

    @property
    def first(self) -> Running:
        return self.runs[0][1]


@dataclass(frozen=True)
class Reach:
    thread: int
    scorer: str
    view: int
    label: str
    offered: bool
    cases: int
    missing: list[Family]
    choosing: list[Family]

    @property
    def have(self) -> int:
        return self.cases - len(self.missing) - len(self.choosing)


@dataclass(frozen=True)
class Graded:
    name: str
    scorer: Scorer
    labels: dict[int, str]
    score: Score | None = None
    findings: list[Finding] = field(default_factory=list[Finding])
    refused: str | None = None

    def label(self, view: int) -> str:
        return self.labels.get(view, f"view {view}")


@dataclass(frozen=True)
class Saved:
    name: str
    digest: str
    what: Literal["created", "a new version", "unchanged"]
    variation: TriedVariation


@dataclass(frozen=True)
class Proposed:
    divergence: Divergence
    proposal: Recipe | Component
    digest: str
    compilation: str | None


@dataclass(frozen=True)
class Corrected:
    behind: Behind
    model: str
    digest: str | None
    compilation: str | None
    refused: str | None


@dataclass(frozen=True)
class Taken:
    taken: dict[str, int]
    kept: dict[str, int]
    choosing: dict[str, list[int]]
    missing: list[str]


@dataclass(frozen=True)
class Written:
    edit: Edit
    what: Literal["created", "a new version", "unchanged"]
    findings: list[Finding]
    cases: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Checked:
    digest: str
    findings: list[Finding]


SAVED: dict[Kept, Literal["created", "a new version", "unchanged"]] = {
    "created": "created",
    "edited": "a new version",
    "unchanged": "unchanged",
}
