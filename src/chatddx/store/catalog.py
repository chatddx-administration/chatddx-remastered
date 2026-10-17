from collections.abc import Collection
from datetime import datetime
from typing import Any, Literal

from chatddx.catalog import (
    Binding,
    Edit,
    Entry,
    EntryField,
    Labels,
    Part,
    RepairPlan,
    Subject,
    Thread,
    families,
    language,
    threads,
)
from chatddx.factors.base import Component, Fingerprint, canonical_bytes
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Vignette
from chatddx.factors.request import Compilation

from .store import Connection, Store

Kept = Literal["created", "edited", "unchanged"]

_THREAD = "t.id, t.kind, t.forked_from, t.by, t.at"
_EDIT = "e.id, e.thread, e.digest, e.compilation, e.based_on, e.by, e.at"
_BINDING = "b.id, b.family, b.source, b.source_id, b.fingerprint, b.by, b.at"


def _thread(row: tuple[Any, ...]) -> Thread:
    id, kind, forked_from, by, at = row
    return Thread(id=id, kind=kind, forked_from=forked_from, by=by, at=at)


def _edit(row: tuple[Any, ...]) -> Edit:
    id, thread, digest, compilation, based_on, by, at = row
    return Edit(
        id=id,
        thread=thread,
        digest=digest,
        compilation=compilation,
        based_on=based_on,
        by=by,
        at=at,
    )


def _binding(row: tuple[Any, ...]) -> Binding:
    id, family, source, source_id, fingerprint, by, at = row
    return Binding(
        id=id,
        family=family,
        vignette=Vignette(
            source=source,
            id=source_id,
            fingerprint=Fingerprint.model_validate(fingerprint),
        ),
        by=by,
        at=at,
    )


def _jsonb(fingerprint: Fingerprint) -> str:
    return canonical_bytes(
        fingerprint.model_dump(mode="json", context={"canonical": True})
    ).decode()


class Rows:
    def __init__(self, conn: Connection) -> None:
        self._conn: Connection = conn
        self._store: Store = Store(conn)

    def get(self, digest: str) -> Component:
        return self._store.get(digest)

    def components(self, digests: Collection[str]) -> list[tuple[str, Component]]:
        rows = self._conn.execute(
            """
            SELECT digest, canonical FROM factor.component
            WHERE digest = ANY(%s::text[]) ORDER BY digest
            """,
            (list(digests),),
        ).fetchall()
        return [(str(d), Registry().add_raw(str(d), str(c).encode())) for d, c in rows]

    def kind(self, digest: str) -> str | None:
        row = self._conn.execute(
            "SELECT kind FROM factor.component WHERE digest = %s", (digest,)
        ).fetchone()
        return None if row is None else str(row[0])

    def compilations(self, skeleton: str) -> list[Compilation]:
        return self._store.compilations(skeleton)

    def thread(self, id: int) -> Thread | None:
        row = self._conn.execute(
            f"SELECT {_THREAD} FROM catalog.thread t WHERE t.id = %s", (id,)
        ).fetchone()
        return None if row is None else _thread(row)

    def threads(self, kind: str) -> list[Thread]:
        rows = self._conn.execute(
            f"SELECT {_THREAD} FROM catalog.thread t WHERE t.kind = %s ORDER BY t.id",
            (kind,),
        ).fetchall()
        return [_thread(r) for r in rows]

    def threads_forked_from(self, edits: Collection[int]) -> list[Thread]:
        rows = self._conn.execute(
            f"""
            SELECT {_THREAD} FROM catalog.thread t
            WHERE t.forked_from = ANY(%s::bigint[]) ORDER BY t.id
            """,
            (list(edits),),
        ).fetchall()
        return [_thread(r) for r in rows]

    def edit(self, id: int) -> Edit | None:
        row = self._conn.execute(
            f"SELECT {_EDIT} FROM catalog.edit e WHERE e.id = %s", (id,)
        ).fetchone()
        return None if row is None else _edit(row)

    def edits(self, threads: Collection[int]) -> list[Edit]:
        rows = self._conn.execute(
            f"""
            SELECT {_EDIT} FROM catalog.edit e
            WHERE e.thread = ANY(%s::bigint[]) ORDER BY e.id
            """,
            (list(threads),),
        ).fetchall()
        return [_edit(r) for r in rows]

    def edits_holding(self, digests: Collection[str]) -> list[Edit]:
        rows = self._conn.execute(
            f"""
            SELECT {_EDIT} FROM catalog.edit e
            WHERE e.digest = ANY(%s::text[]) ORDER BY e.id
            """,
            (list(digests),),
        ).fetchall()
        return [_edit(r) for r in rows]

    def entries(
        self, subjects: Collection[Subject]
    ) -> list[tuple[Subject, Entry, int]]:
        rows = self._conn.execute(
            """
            SELECT thread, family, run, score, field, value, person, present, by
            FROM catalog.entry
            WHERE thread = ANY(%s::bigint[]) OR family = ANY(%s::bigint[])
                OR run = ANY(%s::uuid[]) OR score = ANY(%s::uuid[])
            ORDER BY id
            """,
            (
                [s.thread for s in subjects if s.thread is not None],
                [s.family for s in subjects if s.family is not None],
                [s.run for s in subjects if s.run is not None],
                [s.score for s in subjects if s.score is not None],
            ),
        ).fetchall()
        return [
            (
                Subject(thread=thread, family=family, run=run, score=score),
                Entry(
                    field=EntryField(field), value=value, person=person, present=present
                ),
                int(by),
            )
            for thread, family, run, score, field, value, person, present, by in rows
        ]

    def involving(self, person: int) -> list[Subject]:
        rows = self._conn.execute(
            """
            SELECT DISTINCT thread, family, run, score FROM catalog.entry
            WHERE person = %s AND field IN ('owner', 'collaborator')
            ORDER BY thread, family, run, score
            """,
            (person,),
        ).fetchall()
        return [
            Subject(thread=thread, family=family, run=run, score=score)
            for thread, family, run, score in rows
        ]

    def runs_started(self, person: int, since: datetime) -> int:
        row = self._conn.execute(
            """
            SELECT count(*) FROM catalog.entry
            WHERE run IS NOT NULL AND field = 'owner' AND person = %s AND at >= %s
            """,
            (person, since),
        ).fetchone()
        assert row is not None
        return int(row[0])

    def bindings(self, families: Collection[int]) -> list[Binding]:
        rows = self._conn.execute(
            f"""
            SELECT {_BINDING} FROM catalog.binding b
            WHERE b.family = ANY(%s::bigint[]) ORDER BY b.id
            """,
            (list(families),),
        ).fetchall()
        return [_binding(r) for r in rows]

    def families(self) -> list[int]:
        rows = self._conn.execute("SELECT id FROM catalog.family ORDER BY id")
        return [int(id) for (id,) in rows.fetchall()]

    def bindings_in(self, source: str) -> list[Binding]:
        rows = self._conn.execute(
            f"""
            SELECT {_BINDING} FROM catalog.binding b
            WHERE b.source = %s ORDER BY b.id
            """,
            (source,),
        ).fetchall()
        return [_binding(r) for r in rows]

    def bindings_sharing(self, vignette: Vignette) -> list[Binding]:
        rows = self._conn.execute(
            f"""
            SELECT {_BINDING} FROM catalog.binding b
            WHERE b.source = %s
                AND (b.source_id = %s OR b.fingerprint = %s::jsonb)
            ORDER BY b.id
            """,
            (vignette.source, vignette.id, _jsonb(vignette.fingerprint)),
        ).fetchall()
        return [_binding(r) for r in rows]

    def bound_to(
        self, vignettes: Collection[Vignette], kind: str
    ) -> list[tuple[str, Vignette]]:
        wanted = list(dict.fromkeys(vignettes))
        rows = self._conn.execute(
            """
            SELECT c.digest, v.i FROM factor.component c
            JOIN unnest(%s::text[], %s::text[], %s::jsonb[]) WITH ORDINALITY
                AS v (source, id, fingerprint, i)
                ON c.doc #>> '{vignette,source}' = v.source
                AND c.doc #>> '{vignette,id}' = v.id
                AND c.doc #> '{vignette,fingerprint}' = v.fingerprint
            WHERE c.kind = %s
            ORDER BY c.digest
            """,
            (
                [v.source for v in wanted],
                [v.id for v in wanted],
                [_jsonb(v.fingerprint) for v in wanted],
                kind,
            ),
        ).fetchall()
        return [(str(d), wanted[int(i) - 1]) for d, i in rows]

    def expectations(self, cases: Collection[str]) -> list[str]:
        return [
            str(d)
            for (d,) in self._conn.execute(
                """
                SELECT digest FROM factor.component
                WHERE kind = 'expectation' AND doc ->> 'case' = ANY(%s::text[])
                ORDER BY digest
                """,
                (list(cases),),
            )
        ]

    def languages(self, digests: Collection[str]) -> list[tuple[str, str]]:
        rows = self._conn.execute(
            """
            SELECT digest, value FROM catalog.language
            WHERE digest = ANY(%s::text[]) ORDER BY id
            """,
            (list(digests),),
        ).fetchall()
        return [(str(d), str(v)) for d, v in rows]

    def labels(self, edits: Collection[int]) -> list[tuple[int, Part, int, str]]:
        rows = self._conn.execute(
            """
            SELECT edit, part, position, value FROM catalog.label
            WHERE edit = ANY(%s::bigint[]) ORDER BY id
            """,
            (list(edits),),
        ).fetchall()
        return [(int(e), part, int(p), str(v)) for e, part, p, v in rows]


class Catalog:
    def __init__(self, conn: Connection) -> None:
        self._conn: Connection = conn
        self._rows: Rows = Rows(conn)

    def create(
        self,
        digest: str,
        by: int,
        *,
        compilation: str | None = None,
        forked_from: int | None = None,
        name: str | None = None,
        owner: int | None = None,
        labels: Labels | None = None,
    ) -> Edit:
        named = None if name is None else Entry(field=EntryField.NAME, value=name)
        owned = Entry(field=EntryField.OWNER, person=by if owner is None else owner)
        with self._conn.transaction():
            kind = threads.check_create(self._rows, digest)
            row = self._conn.execute(
                """
                INSERT INTO catalog.thread (kind, forked_from, by)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (kind, forked_from, by),
            ).fetchone()
            assert row is not None
            edit = self.edit(row[0], digest, by, compilation=compilation, labels=labels)
            self.note(Subject(thread=edit.thread), owned, by)
            if named is not None:
                self.note(Subject(thread=edit.thread), named, by)
            return edit

    def edit(
        self,
        thread: int,
        digest: str,
        by: int,
        *,
        compilation: str | None = None,
        based_on: int | None = None,
        head: int | None = None,
        labels: Labels | None = None,
    ) -> Edit:
        with self._conn.transaction():
            self._lock(thread)
            threads.check_edit(
                self._rows, thread, digest, based_on=based_on, head=head, labels=labels
            )
            return self._insert(thread, digest, by, compilation, based_on, labels)

    def _insert(
        self,
        thread: int,
        digest: str,
        by: int,
        compilation: str | None,
        based_on: int | None,
        labels: Labels | None,
    ) -> Edit:
        row = self._conn.execute(
            f"""
            INSERT INTO catalog.edit AS e
                (thread, kind, digest, compilation, based_on, by)
            SELECT t.id, t.kind, %s, %s, %s, %s FROM catalog.thread t
            WHERE t.id = %s
            RETURNING {_EDIT}
            """,
            (digest, compilation, based_on, by, thread),
        ).fetchone()
        assert row is not None
        edit = _edit(row)
        for (part, position), value in sorted((labels or {}).items()):
            _ = self._conn.execute(
                """
                INSERT INTO catalog.label (edit, part, position, value, by)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (edit.id, part, position, value, by),
            )
        return edit

    def _lock(self, thread: int) -> None:
        _ = self._conn.execute(
            "SELECT pg_advisory_xact_lock(hashtext('catalog.thread'), %s::int)",
            (thread % 2**31,),
        )

    def keep(
        self,
        digest: str,
        by: int,
        thread: int | None,
        *,
        name: str | None = None,
        compilation: str | None = None,
        forked_from: int | None = None,
        head: int | None = None,
        labels: Labels | None = None,
    ) -> tuple[Edit, Kept]:
        if thread is None:
            created = self.create(
                digest,
                by,
                compilation=compilation,
                forked_from=forked_from,
                name=name,
                labels=labels,
            )
            return created, "created"
        with self._conn.transaction():
            self._lock(thread)
            threads.check_edit(self._rows, thread, digest, head=head, labels=labels)
            current = threads.head(self._rows, thread)
            if threads.holds(self._rows, current, digest, compilation, labels):
                return current, "unchanged"
            edit = self._insert(thread, digest, by, compilation, None, labels)
            return edit, "edited"

    def adopt(
        self, case: str, by: int, *, owner: int | None = None, by_content: bool = True
    ) -> int:
        with self._conn.transaction():
            if (family := families.family_of(self._rows, case)) is not None:
                return family
            vignette = families.check_adoptable(self._rows, case, by_content=by_content)
            row = self._conn.execute(
                "INSERT INTO catalog.family (by) VALUES (%s) RETURNING id", (by,)
            ).fetchone()
            assert row is not None
            family = int(row[0])
            self._bind(family, vignette, by)
            owned = Entry(field=EntryField.OWNER, person=by if owner is None else owner)
            self.note(Subject(family=family), owned, by)
            return family

    def repair(
        self,
        family: int,
        by: int,
        *,
        id: str | None = None,
        fingerprint: Fingerprint | None = None,
    ) -> RepairPlan:
        with self._conn.transaction():
            plan = families.plan_repair(
                self._rows, family, id=id, fingerprint=fingerprint
            )
            self._bind(family, plan.vignette, by)
            _ = Store(self._conn).add(plan.registry, list(plan.registry))
            for thread, digest in plan.moves:
                _ = self.edit(thread, digest, by)
        return plan

    def note(self, subject: Subject, entry: Entry, by: int) -> None:
        threads.check_note(self._rows, subject, entry)
        _ = self._conn.execute(
            """
            INSERT INTO catalog.entry (
                thread, family, run, run_stage, score, score_stage,
                field, value, person, present, by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                subject.thread,
                subject.family,
                subject.run,
                None if subject.run is None else "started",
                subject.score,
                None if subject.score is None else "started",
                entry.field,
                entry.value,
                entry.person,
                entry.present,
                by,
            ),
        )

    def language(self, digest: str, value: str, by: int) -> None:
        kind = language.check_language(self._rows, digest, value)
        _ = self._conn.execute(
            """
            INSERT INTO catalog.language (digest, kind, value, by)
            VALUES (%s, %s, %s, %s)
            """,
            (digest, kind, value, by),
        )

    # src/chatddx/store/migrations/0012-t2-catalog.sql keeps each
    # binding's source, and its id or fingerprint.
    def _bind(self, family: int, vignette: Vignette, by: int) -> None:
        _ = self._conn.execute(
            """
            INSERT INTO catalog.binding (family, source, source_id, fingerprint, by)
            VALUES (%s, %s, %s, %s::jsonb, %s)
            """,
            (
                family,
                vignette.source,
                vignette.id,
                _jsonb(vignette.fingerprint),
                by,
            ),
        )
