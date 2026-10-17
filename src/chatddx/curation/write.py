from collections import Counter
from collections.abc import Collection, Iterable
from functools import partial

from pydantic import JsonValue

from chatddx.catalog import (
    Entry,
    EntryField,
    Kept,
    Labels,
    Part,
    Subject,
    Survey,
    families,
    read,
    threads,
    titles,
)
from chatddx.catalog.language import language_of
from chatddx.factors.base import Fingerprint, StructuralError
from chatddx.factors.cases import Appendix, Case, Vignette, clean
from chatddx.factors.scoring import Expectation
from chatddx.facts import lints
from chatddx.identity import Person, owns
from chatddx.inventory import DirectorySource
from chatddx.store.catalog import Catalog, Rows
from chatddx.store.people import People
from chatddx.store.store import Connection, Store

from .plan import DataCase, Plan, Planned

ARCHIVE = "archive"
VERBS: dict[Kept, str] = {
    "created": "created",
    "edited": "updated",
    "unchanged": "validated",
}


def _gifted(kind: str) -> bool:
    return kind.startswith("chunk.") or kind in ("tool", "skeleton", "expectation")


def short(digest: str) -> str:
    return digest.removeprefix("sha256:")[:6]


class _Init:
    def __init__(self, conn: Connection, plan: Plan, archive: Person) -> None:
        self.store: Store = Store(conn)
        self.catalog: Catalog = Catalog(conn)
        self.rows: Rows = Rows(conn)
        self.plan: Plan = plan
        self.archive: Person = archive
        self.threads: dict[tuple[str, str], int] = {}
        self.families: list[int] = []
        self.landed: dict[str, list[str]] = {}
        self.lines: list[str] = []
        self.surveyed: Survey | None = None
        self.unsettled: set[int] = set()

    def land(self, digest: str, what: str) -> None:
        self.landed.setdefault(digest, []).append(what)

    def note(self, subject: Subject, entry: Entry) -> None:
        self.catalog.note(subject, entry, self.archive.id)

    def sync(
        self,
        subject: Subject,
        tags: Iterable[str] = (),
        description: str | None = None,
        language: str | None = None,
        name: str | None = None,
    ) -> None:
        about = read.about(self.rows, subject)
        if name is not None and about.name != name:
            self.note(subject, Entry(field=EntryField.NAME, value=name))
        for tag in sorted(set(tags) - about.tags):
            self.note(subject, Entry(field=EntryField.TAG, value=tag))
        if dropped := about.tags - set(tags):
            given = read.tags_given(self.rows, subject)
            for tag in sorted(t for t in dropped if given.get(t) == self.archive.id):
                self.note(
                    subject, Entry(field=EntryField.TAG, value=tag, present=False)
                )
        if description is not None and about.description != description:
            self.note(subject, Entry(field=EntryField.DESCRIPTION, value=description))
        if language is not None and about.language != language:
            self.note(subject, Entry(field=EntryField.LANGUAGE, value=language))

    def put(
        self,
        kind: str,
        digest: str,
        found: list[int],
        name: str | None,
        compilation: str | None = None,
        fork_of: int | None = None,
        labels: Labels | None = None,
    ) -> tuple[int, str]:
        what = f"{kind} {name}" if name is not None else kind
        if len(found) > 1:
            raise ValueError(f"the archive has {len(found)} threads for {what}")
        forked_from = None
        if not found and fork_of is not None:
            forked_from = threads.head(self.rows, fork_of).id
        edit, kept = self.catalog.keep(
            digest,
            self.archive.id,
            found[0] if found else None,
            name=name,
            compilation=compilation,
            forked_from=forked_from,
            labels=labels,
        )
        return edit.thread, VERBS[kept]

    def record(self, r: Planned) -> None:
        found = threads.find(self.rows, r.kind, r.name, owner=self.archive.id)
        labels: dict[tuple[Part, int], str] = {
            ("view", i): label for i, label in enumerate(r.labels) if label is not None
        }
        thread, verb = self.put(
            r.kind,
            r.digest,
            found,
            r.name,
            compilation=r.compilation,
            fork_of=None if r.fork_of is None else self.threads[(r.kind, r.fork_of)],
            labels=labels if r.kind == "scorer" else None,
        )
        self.threads[(r.kind, r.name)] = thread
        self.land(r.digest, f"{r.kind} {r.name}")
        self.sync(Subject(thread=thread), r.tags, r.description)
        said = ""
        if r.language is not None and language_of(self.rows, r.digest) != r.language:
            self.catalog.language(r.digest, r.language, self.archive.id)
            said = f", in {r.language}"
        self.lines.append(
            f"[archive {r.kind}] {r.name}: {verb} {short(r.digest)}{said}"
        )
        if found:
            self.forked(r, thread)

    # A thread's origin is set when it is created (put), so a re-run only reports one
    # that differs from the data's.
    def forked(self, r: Planned, thread: int) -> None:
        held = threads.origin(self.rows, thread)
        planned = None if r.fork_of is None else self.threads[(r.kind, r.fork_of)]
        if held == planned:
            return
        was = (
            "no fork" if held is None else f"a fork of {titles.title(self.rows, held)}"
        )
        wants = "nothing" if r.fork_of is None else r.fork_of
        self.lines.append(
            f"[archive {r.kind}] {r.name}: held as {was}; the data forks it from {wants}"
        )

    def repair_for(self, source: DirectorySource, id: str) -> str | None:
        if self.surveyed is None:
            listing = {c.vignette.id: c.vignette.fingerprint for c in source.cases()}
            self.surveyed = families.survey(self.rows, source.name, listing)
        at = f"at source {source.name!r}; repair-data rebinds family"
        for family, old, new in self.surveyed.renamed:
            if id in (old, new):
                self.unsettled.add(family)
                moved = f"to {new}" if id == old else f"from {old}"
                return f"renamed {moved} {at} {family}"
        for family, changed, _ in self.surveyed.changed:
            if id == changed:
                self.unsettled.add(family)
                return f"changed {at} {family}"
        return None

    def case(
        self, source: DirectorySource, id: str, data: DataCase, schema: str
    ) -> None:
        try:
            raw = source.fetch(id)
        except LookupError:
            if (repair := self.repair_for(source, id)) is not None:
                self.lines.append(f"[archive case] {id}: needs repair: {repair}")
            else:
                self.lines.append(
                    f"[archive case] {id}: missing at source {source.name!r}"
                )
            return
        case = Case(
            vignette=Vignette(
                source=source.name, id=id, fingerprint=Fingerprint.of(raw)
            )
        )
        registry = self.plan.registry
        digest = registry.add(case)
        _ = self.store.add(registry, [digest])
        family = families.family_of(self.rows, digest)
        verb = "validated" if family is not None else "created"
        if family is None:
            try:
                family = self.catalog.adopt(digest, self.archive.id)
            except ValueError as e:
                repair = self.repair_for(source, id) or str(e)
                self.lines.append(f"[archive case] {id}: needs repair: {repair}")
                return
        self.families.append(family)
        self.land(digest, f"case {id}")
        self.sync(Subject(family=family), data.tags, None, data.language, name=id)
        self.lines.append(f"[archive case] {id}: {verb} {short(digest)}")
        self.expect(id, digest, data.targets, schema)
        self.appended(id, case.vignette, data, schema)

    def expect(self, named: str, case: str, data: JsonValue, schema: str) -> None:
        registry = self.plan.registry
        expectation = registry.add(
            Expectation(case=case, expectation_schema=schema, data=data)
        )
        _ = self.store.add(registry, [expectation])
        found = [
            t
            for t in threads.expectations_of(self.rows, case)
            if read.about(self.rows, Subject(thread=t)).owner == self.archive.id
        ]
        thread, verb = self.put("expectation", expectation, found, None)
        self.threads[("expectation", named)] = thread
        self.land(expectation, f"expectation {named}")
        self.sync(Subject(thread=thread))
        self.lines.append(f"[archive expectation] {named}: {verb} {short(expectation)}")

    # An appendix is bound to the vignette its case was just read at, so it's built here
    # rather than planned.
    def appended(
        self, id: str, vignette: Vignette, data: DataCase, schema: str
    ) -> None:
        registry = self.plan.registry
        bound: dict[str, str] = {}
        for name, text in data.appendices.items():
            named = f"{name} for {id}"
            appendix = Appendix(vignette=vignette, text=clean(text, ["newlines.lf@1"]))
            digest = registry.add(appendix)
            _ = self.store.add(registry, [digest])
            found = [
                t
                for t in threads.find(
                    self.rows, "appendix", name, owner=self.archive.id
                )
                if self.binds(t, vignette)
            ]
            thread, verb = self.put("appendix", digest, found, name)
            self.threads[("appendix", named)] = thread
            self.land(digest, f"appendix {named}")
            self.sync(Subject(thread=thread))
            self.lines.append(f"[archive appendix] {named}: {verb} {short(digest)}")
            bound[name] = digest
        for ordered in data.ordered:
            named = f"{id} with {', '.join(ordered.appendices)}"
            case = Case(
                vignette=vignette,
                appendices=tuple(bound[name] for name in ordered.appendices),
            )
            digest = registry.add(case)
            verb = "validated" if self.stored(digest) else "created"
            _ = self.store.add(registry, [digest])
            self.land(digest, f"case {named}")
            self.lines.append(f"[archive case] {named}: {verb} {short(digest)}")
            if ordered.targets is not None:
                self.expect(named, digest, ordered.targets, schema)

    # An appendix is named as its case's file names it, so two cases' may share a name;
    # each is its vignette's, by the vignette's source and id.
    def binds(self, thread: int, vignette: Vignette) -> bool:
        held = self.store.get(threads.head(self.rows, thread).digest)
        assert isinstance(held, Appendix)
        return (held.vignette.source, held.vignette.id) == (
            vignette.source,
            vignette.id,
        )

    def stored(self, digest: str) -> bool:
        try:
            _ = self.store.get(digest)
        except StructuralError:
            return False
        return True

    def leftovers(self, cases: Collection[str]) -> None:
        kept = set(self.threads.values())
        subjects = self.rows.involving(self.archive.id)
        known = read.abouts(self.rows, subjects)

        def named(family: int | None) -> bool:
            if family is None:
                return False
            if family in self.families or family in self.unsettled:
                return True
            about = known.get(Subject(family=family))
            return about is not None and about.name in cases

        lines: list[str] = []
        for subject in subjects:
            about = known[subject]
            if not owns(self.archive.id, about):
                continue
            if subject.thread is not None and subject.thread not in kept:
                kind = threads.thread(self.rows, subject.thread).kind
                if kind == "expectation" and named(self.family_of(subject.thread)):
                    continue
                name = about.name or titles.title(self.rows, subject.thread)
                lines.append(f"[archive {kind}] {name}: not in the data")
            elif subject.family is not None and not named(subject.family):
                name = about.name or f"family {subject.family}"
                lines.append(f"[archive case] {name}: not in the data")
        self.lines += sorted(lines)

    def family_of(self, expectation_thread: int) -> int | None:
        head = threads.head(self.rows, expectation_thread)
        expectation = self.store.get(head.digest)
        assert isinstance(expectation, Expectation)
        return families.family_of(self.rows, expectation.case)

    def lint(self) -> None:
        registry, facts, digests = self.plan.registry, self.plan.facts, [*self.landed]
        findings = lints(registry, facts, digests, partial(language_of, self.rows))
        for f in findings:
            what = ", ".join(self.landed.get(f.subject or "") or [str(f.subject)])
            self.lines.append(f"[lint {f.level}] {what}: {f.code}: {f.message}")
        n = len(findings)
        self.lines.append(
            f"[lint] {n} finding{'' if n == 1 else 's'} in {len(digests)} components"
        )

    def share(self, user: Person) -> None:
        subjects = [Subject(thread=t) for t in self.threads.values()]
        subjects += [Subject(family=f) for f in self.families]
        known = read.abouts(self.rows, subjects)
        shared = 0
        for subject in subjects:
            if user.id not in known[subject].collaborators:
                self.note(subject, Entry(field=EntryField.COLLABORATOR, person=user.id))
                shared += 1
        self.lines.append(
            f"[share] {shared} of {len(subjects)} archive threads and families with "
            + f"{user.login}"
        )

    def giftbag(self, user: Person) -> None:
        for (kind, name), thread in self.threads.items():
            if not _gifted(kind):
                continue
            forks = {
                t: read.about(self.rows, Subject(thread=t))
                for t in threads.forks(self.rows, thread)
            }
            mine = {t: about for t, about in forks.items() if about.owner == user.id}
            if any(not about.deleted for about in mine.values()):
                self.lines.append(f"[giftbag {kind}] {name}: kept")
                continue
            if kind == "expectation" and self._expecting(user, thread):
                self.lines.append(f"[giftbag {kind}] {name}: kept their own")
                continue
            if mine:
                restored = max(mine)
                self.catalog.note(
                    Subject(thread=restored),
                    Entry(field=EntryField.DELETED, present=False),
                    user.id,
                )
                self.lines.append(f"[giftbag {kind}] {name}: restored")
                continue
            head = threads.head(self.rows, thread)
            about = read.about(self.rows, Subject(thread=thread))
            _ = self.catalog.create(
                head.digest,
                user.id,
                compilation=head.compilation,
                forked_from=head.id,
                name=about.name,
            )
            self.lines.append(f"[giftbag {kind}] {name}: forked {short(head.digest)}")

    def _expecting(self, user: Person, thread: int) -> bool:
        head = self.store.get(threads.head(self.rows, thread).digest)
        assert isinstance(head, Expectation)
        case, schema = head.case, head.expectation_schema
        return any(
            owns(user.id, a)
            for _, a in threads.expecting(self.rows, [case], schema)[case]
        )


def _what(rows: Rows, subject: Subject) -> str:
    if subject.thread is not None:
        return f"thread {threads.thread(rows, subject.thread).kind}"
    return "family" if subject.family is not None else "run" if subject.run else "score"


def wipe(conn: Connection, user: Person) -> list[str]:
    deleted: Counter[str] = Counter()
    unshared: Counter[str] = Counter()
    with conn.transaction():
        catalog, rows = Catalog(conn), Rows(conn)
        for subject in rows.involving(user.id):
            about = read.about(rows, subject)
            if owns(user.id, about):
                catalog.note(subject, Entry(field=EntryField.DELETED), user.id)
                deleted[_what(rows, subject)] += 1
            if user.id in about.collaborators:
                catalog.note(
                    subject,
                    Entry(field=EntryField.COLLABORATOR, person=user.id, present=False),
                    user.id,
                )
                unshared[_what(rows, subject)] += 1
    return [
        f"[wipe {what}] {user.login}: deleted {deleted[what]}, unshared {unshared[what]}"
        for what in sorted(deleted | unshared)
    ] or [f"[wipe] {user.login}: nothing to delete or unshare"]


def init(
    conn: Connection,
    plan: Plan,
    cases: dict[str, DataCase],
    source: DirectorySource,
    user: Person,
    giftbag: bool = False,
) -> list[str]:
    schemas = [r for r in plan.records if r.kind == "expectation_schema"]
    if len(schemas) != 1:
        raise ValueError("a data set needs exactly one expectation schema")
    with conn.transaction():
        people = People(conn)
        archive = people.find(ARCHIVE) or people.add(ARCHIVE, "Archive")
        writer = _Init(conn, plan, archive)
        compilations = [r.compilation for r in plan.records if r.compilation]
        _ = writer.store.add(
            plan.registry,
            [*(r.digest for r in plan.records), *compilations, *plan.compilations],
        )
        for r in plan.records:
            writer.record(r)
        writer.lines += [f"[skipped] {s}" for s in plan.skipped]
        writer.lines += [f"[untranslated] {s}" for s in plan.untranslated]
        for id, data in cases.items():
            writer.case(source, id, data, schemas[0].digest)
        writer.leftovers(cases)
        writer.share(user)
        if giftbag:
            writer.giftbag(user)
        writer.lint()
        return writer.lines
