from collections.abc import Collection
from typing import Protocol

from chatddx.factors.base import Component
from chatddx.factors.cases import Vignette
from chatddx.factors.request import Compilation

from .model import (
    About,
    Binding,
    Edit,
    Entry,
    EntryField,
    Labels,
    Part,
    Subject,
    Thread,
)


class Reader(Protocol):
    def get(self, digest: str) -> Component: ...

    def components(self, digests: Collection[str]) -> list[tuple[str, Component]]: ...

    def kind(self, digest: str) -> str | None: ...

    def compilations(self, skeleton: str) -> list[Compilation]: ...

    def thread(self, id: int) -> Thread | None: ...

    def threads(self, kind: str) -> list[Thread]: ...

    def threads_forked_from(self, edits: Collection[int]) -> list[Thread]: ...

    def edit(self, id: int) -> Edit | None: ...

    def edits(self, threads: Collection[int]) -> list[Edit]: ...

    def edits_holding(self, digests: Collection[str]) -> list[Edit]: ...

    def entries(
        self, subjects: Collection[Subject]
    ) -> list[tuple[Subject, Entry, int]]: ...

    def bindings(self, families: Collection[int]) -> list[Binding]: ...

    def bindings_in(self, source: str) -> list[Binding]: ...

    def bindings_sharing(self, vignette: Vignette) -> list[Binding]: ...

    def bound_to(
        self, vignettes: Collection[Vignette], kind: str
    ) -> list[tuple[str, Vignette]]: ...

    def expectations(self, cases: Collection[str]) -> list[str]: ...

    def languages(self, digests: Collection[str]) -> list[tuple[str, str]]: ...

    def labels(self, edits: Collection[int]) -> list[tuple[int, Part, int, str]]: ...


def heads_of(rows: Reader, threads: Collection[int]) -> dict[int, Edit]:
    found = {e.thread: e for e in rows.edits(threads)}
    return {t: found[t] for t in sorted(found)}


def heads_holding(rows: Reader, digests: Collection[str]) -> dict[int, Edit]:
    wanted = set(digests)
    held = heads_of(rows, {e.thread for e in rows.edits_holding(wanted)})
    return {t: h for t, h in held.items() if h.digest in wanted}


def abouts(rows: Reader, subjects: Collection[Subject]) -> dict[Subject, About]:
    entries: dict[Subject, list[Entry]] = {s: [] for s in subjects}
    for subject, entry, _ in rows.entries(subjects):
        entries[subject].append(entry)
    return {s: About.of(e) for s, e in entries.items()}


def tags_given(rows: Reader, subject: Subject) -> dict[str, int]:
    given: dict[str, int] = {}
    for _, entry, by in rows.entries([subject]):
        if entry.field == EntryField.TAG:
            assert entry.value is not None
            if entry.present:
                given[entry.value] = by
            else:
                _ = given.pop(entry.value, None)
    return given


def about(rows: Reader, subject: Subject) -> About:
    return abouts(rows, [subject])[subject]


def labels(rows: Reader, edit: int) -> Labels:
    return {(part, position): value for _, part, position, value in rows.labels([edit])}
