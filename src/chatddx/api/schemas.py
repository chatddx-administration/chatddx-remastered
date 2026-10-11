from datetime import datetime
from typing import Annotated, ClassVar, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from chatddx.bench import PARTS, Outcome
from chatddx.factors import base as factors
from chatddx.identity import Person, Role


class _Schema(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class SignIn(_Schema):
    login: str
    password: str


class Me(_Schema):
    id: int
    login: str
    name: str
    roles: list[Role]

    @classmethod
    def of(cls, person: Person) -> Self:
        return cls(
            id=person.id,
            login=person.login,
            name=person.name,
            roles=sorted(person.roles),
        )


class SignedIn(_Schema):
    token: str
    person: Me


class Edit(_Schema):
    id: int
    digest: str
    compilation: str | None
    based_on: int | None
    by: str
    at: datetime


class Thread(_Schema):
    id: int
    kind: str
    name: str | None
    title: str
    owner: str | None
    tags: list[str]
    head: Edit


class ThreadDetail(Thread):
    description: str | None
    collaborators: list[str]
    language: str | None
    forked_from: int | None
    recipe: JsonValue
    deleted: bool


# What is said about a thread, as it is to hold afterwards; a field not given stays.
class Said(_Schema):
    name: str | None = Field(
        None, description="null takes the name away, and the title takes over"
    )
    description: str | None = Field(None, description="replaced, never taken away")
    tags: list[str] | None = Field(None, description="its tags")
    collaborators: list[str] | None = Field(
        None, description="the logins it is shared with"
    )
    deleted: bool | None = None


type Chunk = Annotated[
    str | None,
    Field(description="a chunk's digest; empty or null takes an optional part out"),
]


# The parts a variation replaces over a configuration; a part not given is its own.
class Parts(_Schema):
    instructions: Chunk = None
    few_shot: Chunk = None
    prompt: Chunk = None
    output: Chunk = None
    sampling: Chunk = None
    reasoning: Chunk = None
    passthrough: Chunk = None
    translations: Chunk = None
    toolset: Chunk = None

    def given(self) -> dict[str, str | None]:
        return {
            p: getattr(self, p) or None for p in PARTS if p in self.model_fields_set
        }


class Varying(Parts):
    endpoint: str | None = Field(None, description="to render and lint it for")
    tag: list[str] = Field(
        default_factory=list[str],
        description="the cases its reach is over: any of these, else every one",
    )
    seed: int | None = Field(None, description="drawn when not given")


type ComponentBody = Annotated[
    dict[str, JsonValue],
    Field(
        description="a component's JSON as GET /api/components/{digest} gives its "
        + "body, kind included"
    ),
]
type Language = Annotated[
    str | None,
    Field(description="the language of the text the component holds, such as 'sv'"),
]


class NewThread(_Schema):
    component: ComponentBody | None = None
    recipe: dict[str, JsonValue] | None = Field(
        None,
        description="for a new configuration: the recipe's parts by digest, its "
        + "purpose and its appendix layout, as a configuration's recipe reads",
    )
    name: str = Field(min_length=1)
    language: Language = None

    @model_validator(mode="after")
    def _one(self) -> Self:
        if (self.component is None) == (self.recipe is None):
            raise ValueError("a new thread holds a component or a recipe, not both")
        return self


# A configuration is forked with parts replaced, any other kind with a component.
class NewFork(_Schema):
    name: str = Field(min_length=1)
    parts: Parts = Parts()
    component: ComponentBody | None = Field(
        None, description="what the fork starts from in place of the head"
    )
    language: Language = None


class NewEdit(_Schema):
    head: int = Field(description="the edit the change was made on: the head seen")
    parts: Parts = Parts()
    component: ComponentBody | None = None
    language: Language = None


class Part(_Schema):
    part: str
    digest: str | None
    title: str | None
    summary: str | None
    replaced: bool


class Finding(_Schema):
    level: Literal["info", "warning"]
    code: str
    message: str
    subject: str | None

    @classmethod
    def of(cls, finding: factors.Finding) -> Self:
        return cls.model_validate(finding.model_dump())


# A path where a fork's head differs from its base, with each side's value.
class Varied(_Schema):
    path: str
    base: JsonValue
    fork: JsonValue


# What following a fork's origin would keep.
class Proposal(_Schema):
    base: Edit
    origin_head: Edit
    varies: list[Varied]
    recipe: JsonValue = Field(description="for a configuration, what it compiles from")
    component: JsonValue = Field(description="for another kind, its body")
    digest: str
    compilation: str | None


class NewFollow(_Schema):
    head: int = Field(description="the edit the change was made on: the head seen")
    language: Language = None


# What was written, with what the lints say of its component.
class MadeThread(ThreadDetail):
    findings: list[Finding]


class MadeEdit(Edit):
    findings: list[Finding]


# What one view of a scorer gets from the variation: whether its output offers what the
# view reads, and the families without an expectation it picks something from.
class Reach(_Schema):
    scorer: int
    name: str
    view: int
    label: str
    offered: bool
    cases: int
    missing: list[int]
    choosing: list[int]


class Variation(_Schema):
    head: Edit
    skeleton: str
    greedy: bool
    parts: list[Part] | None
    seed: int
    request: dict[str, JsonValue]
    findings: list[Finding] | None
    reach: list[Reach]


class Family(_Schema):
    id: int
    name: str
    owner: str | None
    tags: list[str]
    language: str | None
    case: str


# The expectation the person's case is scored against under one schema, or why there's
# none to tell: several to choose from.
class Expected(_Schema):
    expectation_schema: str
    title: str
    expectation: str | None
    data: JsonValue
    ambiguous: str | None
    shared: list[Thread] = Field(
        description="the expectation threads of others, shared with the person, they "
        + "could take"
    )


class NewTakes(_Schema):
    families: list[int] = Field(min_length=1, description="the cases, by family")
    expectation_schema: str
    owner: str | None = Field(None, description="a login: that owner's only")


# Keyed by family.
class Taken(_Schema):
    taken: dict[int, int] = Field(description="the thread each was taken into")
    kept: dict[int, int] = Field(description="the person's own, left as it is")
    choosing: dict[int, list[int]] = Field(
        description="shared by several owners: the threads to choose from"
    )
    missing: list[int] = Field(description="none shared")


class NewTake(_Schema):
    replace: bool = Field(
        False,
        description="delete the person's own expectation of the case under that "
        + "schema, in the same write",
    )


class FamilyDetail(Family):
    description: str | None
    collaborators: list[str]
    appendices: list[str]
    expectations: list[Expected]


class Vignette(_Schema):
    source: str
    id: str
    text: str
    # Whether the source holds another text than the case was made from; unknown for a
    # keyed fingerprint.
    drifted: bool | None


class Endpoint(_Schema):
    name: str
    engine: str
    title: str | None
    model: str | None
    url: str | None
    host: str | None
    max_jobs: int
    credential: str | None
    cleared_for: list[str]
    problem: str | None


class Model(_Schema):
    name: str
    facts: JsonValue
    endpoints: list[str]


class Component(_Schema):
    digest: str
    kind: str
    title: str
    body: JsonValue


class NewRun(_Schema):
    configuration: int
    parts: Parts = Parts()
    endpoint: str
    families: list[int] | None = Field(None, description="the cases to run, by family")
    tags: list[str] | None = Field(
        None, description="or the cases of the families with any of these"
    )
    seed: int | None = Field(None, description="drawn when not given")
    score: bool = Field(
        True, description="under every scorer that applies, once it is finished"
    )

    @model_validator(mode="after")
    def _cases(self) -> Self:
        if (self.families is None) == (self.tags is None):
            raise ValueError("a run takes families or tags, and not both")
        return self


class Rig(_Schema):
    distribution: str
    version: str
    revision: str | None


class Run(_Schema):
    id: UUID
    at: datetime
    trial: str
    skeleton: str
    engine: str
    endpoint: str | None
    cases: list[str]
    seeds: list[int]
    described: str
    finished: bool


class Item(_Schema):
    case: str
    replicate: int
    outcome: Outcome
    prompt_tokens: int
    completion_tokens: int


# An item as it was recorded, which is case-derived.
class ItemDetail(Item):
    why: str | None
    vignette: JsonValue
    call: JsonValue
    turns: JsonValue


class ScoredItem(_Schema):
    case: str
    replicate: int
    view: int
    value: float | None


# A run's score under one scorer, or why it gave none: the values, without the scorer's
# detail or findings, which may quote the answer.
class Graded(_Schema):
    scorer: str
    name: str
    score: UUID | None
    labels: list[str]
    means: list[float | None]
    items: list[ScoredItem]
    refused: str | None


class RunDetail(Run):
    rig: Rig
    finished_at: datetime | None
    noted: list[Finding]
    findings: list[Finding]
    items: list[Item]
    scores: list[Graded]


class RenderedAgain(_Schema):
    case: str
    replicate: int
    same: bool
    why: str | None


# The data of each event of a run's stream, by the event's name.


class RunStartedData(_Schema):
    run: UUID
    trial: str
    skeleton: str
    endpoint: str
    cases: list[str]
    seed: int
    greedy: bool


class ItemStartedData(_Schema):
    case: str
    replicate: int
    seed: int


class ItemDeltaData(_Schema):
    case: str
    replicate: int
    kind: Literal["reasoning", "content", "tool_call"]
    text: str
    tokens: int


class ItemToolData(_Schema):
    case: str
    replicate: int
    tool: JsonValue


class ItemEndedData(Item):
    why: str | None


class CanaryEndedData(_Schema):
    phase: str
    canary: int
    call: JsonValue


class RunFinishedData(_Schema):
    findings: list[Finding]


class RunScoredData(_Schema):
    scores: list[Graded]


class ErrorData(_Schema):
    detail: str


EVENTS: dict[str, type[_Schema]] = {
    "run.started": RunStartedData,
    "item.started": ItemStartedData,
    "item.delta": ItemDeltaData,
    "item.tool": ItemToolData,
    "item.ended": ItemEndedData,
    "canary.ended": CanaryEndedData,
    "run.noted": Finding,
    "run.finished": RunFinishedData,
    "run.scored": RunScoredData,
    "error": ErrorData,
}
