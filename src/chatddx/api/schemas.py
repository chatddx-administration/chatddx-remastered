from datetime import datetime
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, JsonValue

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
