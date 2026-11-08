import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Annotated, ClassVar, Protocol, Self, cast, override
from uuid import UUID

from pydantic import AfterValidator, AwareDatetime, Field, JsonValue, PrivateAttr

from chatddx.factors.base import (
    Finding,
    Frozen,
    StructuralError,
    Upgrade,
    canonical_bytes,
    sha256_digest,
    sorted_keys,
    upgraded,
)
from chatddx.factors.cases import CaseRef


def _utc(at: datetime) -> datetime:
    return at.astimezone(UTC)


UtcDatetime = Annotated[AwareDatetime, AfterValidator(_utc)]


def in_order(started: datetime, finished: datetime) -> None:
    if finished < started:
        raise ValueError("finished before it started")


class Record(Frozen):
    sensitive: ClassVar[bool] = True
    schema_version: ClassVar[int] = 1
    upgrades: ClassVar[Mapping[int, Upgrade]] = {}
    _stored: dict[str, JsonValue] | None = PrivateAttr(default=None)

    def canonical_doc(self) -> dict[str, JsonValue]:
        doc = cast(
            dict[str, JsonValue],
            self.model_dump(mode="json", context={"canonical": True}),
        )
        return sorted_keys({**doc, "v": type(self).schema_version})

    @property
    def canonical(self) -> bytes:
        return canonical_bytes(self.canonical_doc())

    def as_stored(self) -> dict[str, JsonValue]:
        """The doc as it was stored, of the version it was stored at, for a record
        parsed from it, else its canonical doc."""
        return self.canonical_doc() if self._stored is None else self._stored

    @classmethod
    def parse(cls, data: bytes | str) -> Self:
        loaded: object = json.loads(data)
        if not isinstance(loaded, dict):
            raise StructuralError(f"{cls.__name__} is not a JSON object")
        stored = cast(dict[str, JsonValue], loaded)
        doc = upgraded(cls.__name__, dict(stored), cls.schema_version, cls.upgrades)
        record = cls.model_validate(doc)
        if stored.get("v") != cls.schema_version:
            record._stored = stored
        return record


class ItemKey(Frozen):
    case: CaseRef
    replicate: int = Field(ge=0)

    @override
    def __hash__(self) -> int:
        return hash((self.case, self.replicate))


class Stage(Protocol):
    @property
    def at(self) -> datetime: ...


def check_log(started: Stage, finished: Stage | None, ids: Iterable[UUID]) -> None:
    if finished is not None:
        in_order(started.at, finished.at)
    if len(set(ids)) > 1:
        raise StructuralError("rows belong to different logs")


def seal_rows(started: Record, **rows: Iterable[Record]) -> str:
    doc: dict[str, JsonValue] = {
        name: sorted((r.as_stored() for r in group), key=canonical_bytes)
        for name, group in rows.items()
    }
    doc["started"] = started.as_stored()
    return sha256_digest(canonical_bytes(sorted_keys(doc)))


class Finished(Protocol):
    @property
    def seal(self) -> str: ...


class Log(Protocol):
    @property
    def finished(self) -> Finished | None: ...

    def seal(self) -> str: ...


def check_seal(log: Log, subject: str) -> list[Finding]:
    finished = log.finished
    if finished is not None and finished.seal != log.seal():
        return [
            Finding.of(
                "ledger.seal",
                "rows changed after the log was sealed",
                subject=subject,
            )
        ]
    return []
