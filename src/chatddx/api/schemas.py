from datetime import datetime
from typing import Annotated, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from chatddx.bench import PARTS
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


class NewFork(_Schema):
    name: str = Field(min_length=1)
    parts: Parts = Parts()


class NewEdit(_Schema):
    parts: Parts = Parts()


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
