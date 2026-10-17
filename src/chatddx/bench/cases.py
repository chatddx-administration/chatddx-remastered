import re
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from chatddx import settings
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.catalog.families import rebind_case
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Appendix, Case, Vignette
from chatddx.factors.scoring import Expectation
from chatddx.identity import sees
from chatddx.inventory import DatabaseSource
from chatddx.store import Texts

from .components import bound, edit_component
from .errors import NotFound, OverQuota
from .model import Family, Written
from .seen import Seen

# A case's title, as src/chatddx/catalog/titles.py:describe_case writes it.
WITH = re.compile(r"^(?P<family>.+?) with (?P<appendices>.+)$")


def appendices_of(seen: Seen, family: int) -> dict[str, str]:
    vignette = seen.current(seen.family_by_id(family).id)
    return {
        about.name: edit.digest
        for edit, about in seen.visible("appendix")
        if about.name is not None
        and resolve(seen.get, edit.digest, Appendix).vignette == vignette
    }


def case_titled(seen: Seen, title: str) -> tuple[Family, str]:
    found = WITH.match(title)
    if found is None:
        family = seen.family(title)
        return family, family.case
    family = seen.family(found["family"])
    names = [name.strip() for name in found["appendices"].split(",")]
    held = appendices_of(seen, family.id)
    if missing := [name for name in names if name not in held]:
        raise NotFound(f"no appendix {', '.join(missing)} of {family.name}")
    vignette = seen.current(family.id)
    made = Case(vignette=vignette, appendices=tuple(held[n] for n in names)).digest
    if made not in seen.cases(family.id):
        raise NotFound(f"no case {title} for {seen.person.login}")
    return family, made


def case_titles(seen: Seen) -> list[str]:
    bare = {
        Case(vignette=resolve(seen.get, edit.digest, Appendix).vignette).digest
        for edit, _ in seen.visible("appendix")
    }
    return sorted(
        seen.title(case)
        for family in seen.families()
        if family.case in bare
        for case in seen.cases(family.id)
        if case != family.case
    )


def appendix(seen: Seen, family: int, text: str) -> Appendix:
    found = seen.family_by_id(family)
    return bound(seen, Appendix(vignette=seen.current(found.id), text=text))


def case(seen: Seen, family: int, appendices: Sequence[str]) -> str:
    found = seen.family_by_id(family)
    for digest in appendices:
        held = seen.catalog.containing(digest)
        if not any(sees(seen.person.id, seen.about(e.thread)) for e in held):
            raise NotFound(f"no appendix {digest} for {seen.person.login}")
    made = Case(vignette=seen.current(found.id), appendices=tuple(appendices))
    registry = seen.store.load(appendices)
    _ = seen.store.add(registry, [registry.add(made)])
    return made.digest


def replacement(seen: Seen, case: str) -> str:
    family = seen.catalog.family(case)
    if family is None:
        raise NotFound(f"no case {case} for {seen.person.login}")
    found = seen.family_by_id(family)
    current = seen.current(found.id)
    held = resolve(seen.get, case, Case)
    if held.vignette == current:
        raise ValueError(f"{case} is at its family's current vignette already")
    made, appendices = rebind_case(held, current, seen.get)
    registry = Registry()
    for appendix in appendices.values():
        _ = registry.add(appendix)
    _ = seen.store.add(registry, [registry.add(made)])
    return made.digest


def type_case(
    seen: Seen,
    text: str,
    *,
    language: str,
    name: str | None = None,
    source: str | None = None,
) -> Family:
    if not text.strip():
        raise ValueError("a typed case holds text")
    if "\0" in text:
        raise ValueError("a typed case may not hold U+0000, which can't be stored")
    if len(text) > settings.TYPED_TEXT_LIMIT:
        raise ValueError(
            f"a typed case holds at most {settings.TYPED_TEXT_LIMIT} characters, "
            + f"not {len(text)}"
        )
    if name == "":
        raise ValueError("a name can't be empty: none leaves the case unnamed")
    entries = [Entry(field=EntryField.LANGUAGE, value=language)]
    if name is not None:
        entries.append(Entry(field=EntryField.NAME, value=name))
    try:
        into = seen.inventory.source(source, DatabaseSource).name
    except LookupError as e:
        raise ValueError(str(e)) from None
    texts = Texts(seen.conn)
    since = datetime.now(UTC) - timedelta(days=1)
    if (typed := texts.typed_since(seen.person.id, since)) >= settings.TYPED_PER_DAY:
        raise OverQuota(
            f"{seen.person.login} has typed {typed} cases in the last day, as many "
            + "as a day takes"
        )
    with seen.conn.transaction():
        id = texts.add(into, text, seen.person.id)
        vignette = Vignette(
            source=into, id=id, fingerprint=Fingerprint.of(text.encode())
        )
        registry = Registry()
        case = registry.add(Case(vignette=vignette))
        _ = seen.store.add(registry, [case])
        family = seen.catalog.adopt(case, seen.person.id, by_content=False)
        for entry in entries:
            seen.catalog.note(Subject(family=family), entry, seen.person.id)
    return seen.family_by_id(family)


def takes_typed(seen: Seen, endpoint: str) -> bool:
    try:
        into = seen.inventory.source(kind=DatabaseSource)
    except LookupError:
        return False
    return not into.sensitive or into.name in seen.inventory.cleared.get(endpoint, ())


def carry(seen: Seen, thread: int, head: int, case: str) -> Written:
    edit, _, word = seen.worded(thread)
    if word != "expectation":
        raise ValueError(f"{word} {thread} isn't an expectation")
    held = resolve(seen.get, edit.digest, Expectation)
    family = seen.catalog.family(held.case)
    if family is None or seen.catalog.family(case) != family:
        raise ValueError(f"{case} isn't a case of the family {held.case} is of")
    carried = Expectation(
        case=case, expectation_schema=held.expectation_schema, data=held.data
    )
    return edit_component(seen, thread, head, carried)
