import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from enum import StrEnum
from typing import ClassVar, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from chatddx.factors.base import Fingerprint, language_tag
from chatddx.factors.cases import Vignette
from chatddx.factors.request import RECIPE_PARTS

# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats these kinds.
THREAD_KINDS = frozenset(
    {
        "chunk.instructions",
        "chunk.few_shot",
        "chunk.prompt",
        "chunk.output",
        "chunk.sampling",
        "chunk.reasoning",
        "chunk.passthrough",
        "chunk.translations",
        "chunk.toolset",
        "tool",
        "skeleton",
        "trial",
        "judge",
        "scorer",
        "scoring",
        "appendix",
        "expectation",
        "model.local",
        "model.remote",
        "engine.local",
        "engine.remote",
        "facts",
        "expectation_schema",
        "canary_set",
    }
)


# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats these kinds.
LANGUAGE_KINDS = frozenset(
    {
        "chunk.instructions",
        "chunk.few_shot",
        "chunk.prompt",
        "chunk.output",
        "chunk.toolset",
        "skeleton",
    }
)


# Duplication: src/chatddx/store/migrations/0026-t2-catalog-run-variation.sql repeats
# these patterns.
_VARIED = re.compile(r"^[1-9][0-9]{0,17}$")
_WITH = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_REPLACED = re.compile(rf"^({'|'.join(RECIPE_PARTS)})=(sha256:[0-9a-f]{{64}})?$")


class MovedOn(ValueError):
    pass


class EntryField(StrEnum):
    NAME = "name"
    DESCRIPTION = "description"
    TAG = "tag"
    OWNER = "owner"
    COLLABORATOR = "collaborator"
    DELETED = "deleted"
    LANGUAGE = "language"
    VARIED = "varied"
    REPLACED = "replaced"
    WITH = "with"


RUN_FIELDS = frozenset({EntryField.VARIED, EntryField.REPLACED, EntryField.WITH})


Part = Literal["view", "resource"]
Labels = Mapping[tuple[Part, int], str]


class _Frozen(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


class Thread(_Frozen):
    id: int
    kind: str
    forked_from: int | None
    by: int
    at: datetime


class Edit(_Frozen):
    id: int
    thread: int
    digest: str
    compilation: str | None
    based_on: int | None
    by: int
    at: datetime


class Divergence(_Frozen):
    base: Edit
    origin_head: Edit
    varies: dict[str, tuple[JsonValue, JsonValue]]

    @property
    def moved(self) -> bool:
        return self.origin_head.id != self.base.id


class Binding(_Frozen):
    id: int
    family: int
    vignette: Vignette
    by: int
    at: datetime


class Behind(_Frozen):
    path: str
    digest: str
    head: Edit | None = None
    binding: Binding | None = None
    replacement: str | None = None

    @model_validator(mode="after")
    def _one(self) -> Self:
        if (self.head is None) == (self.binding is None):
            raise ValueError("behind either a newer head or a newer binding")
        if (self.binding is None) != (self.replacement is None):
            raise ValueError(
                "a replacement case goes with a newer binding, and only with it"
            )
        return self


class Survey(_Frozen):
    unchanged: tuple[int, ...] = ()
    changed: tuple[tuple[int, str, Fingerprint], ...] = ()
    renamed: tuple[tuple[int, str, str], ...] = ()
    new: tuple[str, ...] = ()
    gone: tuple[int, ...] = ()


class Subject(_Frozen):
    thread: int | None = None
    family: int | None = None
    run: UUID | None = None
    score: UUID | None = None

    @model_validator(mode="after")
    def _one(self) -> Self:
        if [self.thread, self.family, self.run, self.score].count(None) != 3:
            raise ValueError(
                "a subject is exactly one of a thread, a family, a run or a score"
            )
        return self


class Entry(_Frozen):
    field: EntryField
    value: str | None = None
    person: int | None = None
    present: bool = True

    @model_validator(mode="after")
    def _shape(self) -> Self:
        text = self.field in (EntryField.TAG, EntryField.LANGUAGE, *RUN_FIELDS) or (
            self.field in (EntryField.NAME, EntryField.DESCRIPTION) and self.present
        )
        person = self.field in (EntryField.OWNER, EntryField.COLLABORATOR)
        removable = self.field in (
            EntryField.NAME,
            EntryField.DESCRIPTION,
            EntryField.TAG,
            EntryField.COLLABORATOR,
            EntryField.DELETED,
        )
        if (self.value is not None) != text or (self.person is not None) != person:
            raise ValueError(f"wrong value or person for {self.field}")
        if not (self.present or removable):
            raise ValueError(f"{self.field} can't be removed, only replaced")
        if (
            self.field in (EntryField.NAME, EntryField.DESCRIPTION, EntryField.TAG)
            and self.value == ""
        ):
            raise ValueError(f"{self.field} can't be empty")
        if self.field == EntryField.LANGUAGE:
            _ = language_tag(self.value or "")
        if self.field == EntryField.VARIED and not _VARIED.match(self.value or ""):
            raise ValueError(f"{self.value!r} is not an edit's id")
        if self.field == EntryField.REPLACED and not _REPLACED.match(self.value or ""):
            raise ValueError(
                f"{self.value!r} is not PART=DIGEST, or PART= for a part taken out"
            )
        if self.field == EntryField.WITH and not _WITH.match(self.value or ""):
            raise ValueError(f"{self.value!r} is not a run's id")
        return self

    @classmethod
    def varied(cls, edit: int) -> Self:
        return cls(field=EntryField.VARIED, value=str(edit))

    @classmethod
    def replaced(cls, part: str, digest: str | None) -> Self:
        return cls(field=EntryField.REPLACED, value=f"{part}={digest or ''}")

    @classmethod
    def started_with(cls, run: UUID) -> Self:
        return cls(field=EntryField.WITH, value=str(run))


class About(_Frozen):
    name: str | None = None
    description: str | None = None
    tags: frozenset[str] = frozenset()
    owner: int | None = None
    collaborators: frozenset[int] = frozenset()
    deleted: bool = False
    language: str | None = None
    varied: int | None = None
    replaced: dict[str, str | None] = Field(default_factory=dict[str, str | None])
    started_with: UUID | None = None

    @classmethod
    def of(cls, entries: Iterable[Entry]) -> Self:
        name = description = language = None
        owner = varied = started_with = None
        replaced: dict[str, str | None] = {}
        tags: set[str] = set()
        collaborators: set[int] = set()
        deleted = False
        for e in entries:
            match e.field:
                case EntryField.NAME:
                    name = e.value
                case EntryField.DESCRIPTION:
                    description = e.value
                case EntryField.TAG:
                    assert e.value is not None
                    _toggle(tags, e.value, e.present)
                case EntryField.OWNER:
                    owner = e.person
                case EntryField.COLLABORATOR:
                    assert e.person is not None
                    _toggle(collaborators, e.person, e.present)
                case EntryField.DELETED:
                    deleted = e.present
                case EntryField.LANGUAGE:
                    language = e.value
                case EntryField.VARIED:
                    varied = int(e.value or "")
                case EntryField.REPLACED:
                    part, digest = (e.value or "").split("=")
                    replaced[part] = digest or None
                case EntryField.WITH:
                    started_with = UUID(e.value)
        return cls(
            name=name,
            description=description,
            tags=frozenset(tags),
            owner=owner,
            collaborators=frozenset(collaborators),
            deleted=deleted,
            language=language,
            varied=varied,
            replaced={p: replaced[p] for p in RECIPE_PARTS if p in replaced},
            started_with=started_with,
        )


def _toggle[T](members: set[T], member: T, present: bool) -> None:
    if present:
        members.add(member)
    else:
        members.discard(member)
