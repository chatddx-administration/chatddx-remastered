from dataclasses import dataclass, field
from typing import Literal

from chatddx.catalog import About, Behind, Divergence, Edit, Part
from chatddx.factors.base import Component, Finding
from chatddx.factors.cases import Vignette
from chatddx.factors.engine import Model
from chatddx.factors.request import CHUNK_PARTS, Recipe, Skeleton, SlotName
from chatddx.factors.scoring import Scorer
from chatddx.inventory import EndpointSpec
from chatddx.ledger import Score
from chatddx.runner import Running
from chatddx.store import Kept

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
    "model": ("model.local", "model.remote"),
    "engine": ("engine.local", "engine.remote"),
    "facts": ("facts",),
}


def word_of(kind: str | None) -> str:
    return next((w for w, held in KINDS.items() if kind in held), "thread")


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
MODEL = "‹model›"


@dataclass(frozen=True)
class Endpoint:
    name: str
    spec: EndpointSpec
    model: Model

    @property
    def engine(self) -> str:
        return self.spec.engine


@dataclass(frozen=True)
class Family:
    id: int
    about: About
    vignette: Vignette
    cases: tuple[str, ...]

    @property
    def case(self) -> str:
        return self.cases[0]

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
class Proposed:
    divergence: Divergence
    proposal: Recipe | Component
    digest: str
    compilation: str | None


@dataclass(frozen=True)
class Moved:
    facts: Behind | None
    model: Behind | None
    about: str
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
