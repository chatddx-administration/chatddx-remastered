from dataclasses import dataclass, field
from typing import Literal

from chatddx.catalog import About, Edit, Kept, Part, Variation
from chatddx.factors.base import Component, Finding
from chatddx.factors.request import Recipe, SlotName
from chatddx.factors.scoring import Scorer
from chatddx.ledger import Score

from .variation import PARTS, TriedVariation

# The kinds of thread each word names: a configuration is a skeleton thread, a part is a
# chunk of that part, and an engine is local or remote.
KINDS: dict[str, tuple[str, ...]] = {
    "configuration": ("skeleton",),
    **{part: (f"chunk.{part}",) for part in PARTS},
    "tool": ("tool",),
    "scorer": ("scorer",),
    "judge": ("judge",),
    "expectation_schema": ("expectation_schema",),
    "expectation": ("expectation",),
    "appendix": ("appendix",),
    "canary_set": ("canary_set",),
    "model": ("model",),
    "engine": ("engine.local", "engine.remote"),
}

# The kinds a person writes as components. A configuration is written as a variation.
WRITTEN: frozenset[str] = frozenset(
    {*(f"chunk.{part}" for part in PARTS), "expectation", "appendix", "scorer"}
)

LABELLED: tuple[Part, ...] = ("view", "resource")

COMPILED_LANGUAGE = "a compiled configuration's language comes from its recipe"

# What stands in for each slot in a request rendered to be looked at.
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


# What one view of a scorer gets from a variation's answers and the cases' expectations.
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


# A run's score under one scorer, or why it couldn't be scored.
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


# What following a fork's origin would keep: the origin's head with the fork's changes on
# top, as a recipe or a component, and the digest it comes to, with the compilation that
# makes it for a recipe.
@dataclass(frozen=True)
class Proposed:
    variation: Variation
    proposal: Recipe | Component
    digest: str
    compilation: str | None


# What taking expectations for some cases did with each: by case, the thread the person
# took one into, their own thread left as it was, the shared threads of several owners
# to pick from, and the cases nothing shared has one for.
@dataclass(frozen=True)
class Taken:
    taken: dict[str, int]
    kept: dict[str, int]
    choosing: dict[str, list[int]]
    missing: list[str]


# A component kept in a thread of the person's own, and what the lints say of it.
@dataclass(frozen=True)
class Written:
    edit: Edit
    what: Literal["created", "a new version", "unchanged"]
    findings: list[Finding]
    # For an appendix's edit, each case that held the old version and its replacement.
    cases: dict[str, str] = field(default_factory=dict)


SAVED: dict[Kept, Literal["created", "a new version", "unchanged"]] = {
    "created": "created",
    "edited": "a new version",
    "unchanged": "unchanged",
}
