from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.catalog.families import rebind_case
from chatddx.core import settings
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Appendix, Case, Vignette
from chatddx.factors.scoring import Expectation
from chatddx.inventory import DatabaseSource
from chatddx.store import Texts

from .components import bound, edit_component
from .errors import NotFound, OverQuota
from .model import Family, Written
from .view import View


# An appendix of `text` for `family`, a case the person sees, bound to its current
# vignette; written with `new`, `fork_component` or `edit_component`.
def appendix(view: View, family: int, text: str) -> Appendix:
    found = view.family_by_id(family)
    return bound(view, Appendix(vignette=view.current(found.id), text=text))


# A case of `family` with `appendices` in order, each one the person sees, stored at its
# current vignette. Nothing is written in the catalog, since a case belongs to its family
# by its vignette.
def case(view: View, family: int, appendices: Sequence[str]) -> str:
    found = view.family_by_id(family)
    for digest in appendices:
        held = view.catalog.containing(digest)
        if not any(view.about(e.thread).shows(view.person.id) for e in held):
            raise NotFound(f"no appendix {digest} for {view.person.login}")
    made = Case(vignette=view.current(found.id), appendices=tuple(appendices))
    registry = view.store.load(appendices)
    _ = view.store.add(registry, [registry.add(made)])
    return made.digest


# The replacement of `case`, left at an earlier vignette of its family by a repair: the
# same appendix texts at the current one, stored.
def replacement(view: View, case: str) -> str:
    family = view.catalog.family(case)
    if family is None:
        raise NotFound(f"no case {case} for {view.person.login}")
    found = view.family_by_id(family)
    current = view.current(found.id)
    held = resolve(view.get, case, Case)
    if held.vignette == current:
        raise ValueError(f"{case} is at its family's current vignette already")
    made, appendices = rebind_case(held, current, view.get)
    registry = Registry()
    for appendix in appendices.values():
        _ = registry.add(appendix)
    _ = view.store.add(registry, [registry.add(made)])
    return made.digest


# A case the person typed: kept as a text of `source`, else of the World's one database
# source, with its case and a family of the person's own, named `name` and in `language`
# when given, all at once.
def type_case(
    view: View,
    text: str,
    *,
    name: str | None = None,
    language: str | None = None,
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
    entries = [] if name is None else [Entry(field=EntryField.NAME, value=name)]
    if language is not None:
        entries.append(Entry(field=EntryField.LANGUAGE, value=language))
    into = _typed_into(view, source)
    texts = Texts(view.conn)
    since = datetime.now(UTC) - timedelta(days=1)
    if (typed := texts.typed_since(view.person.id, since)) >= settings.TYPED_PER_DAY:
        raise OverQuota(
            f"{view.person.login} has typed {typed} cases in the last day, as many "
            + "as a day takes"
        )
    with view.conn.transaction():
        id = texts.add(into, text, view.person.id)
        vignette = Vignette(
            source=into, id=id, fingerprint=Fingerprint.of(text.encode())
        )
        registry = Registry()
        case = registry.add(Case(vignette=vignette))
        _ = view.store.add(registry, [case])
        family = view.catalog.adopt(case, view.person.id, by_content=False)
        for entry in entries:
            view.catalog.note(Subject(family=family), entry, view.person.id)
    return view.family_by_id(family)


def _typed_into(view: View, source: str | None) -> str:
    held = sorted(
        s.name for s in view.inventory.sources.values() if isinstance(s, DatabaseSource)
    )
    if source is not None and source not in held:
        raise ValueError(f"{source!r} isn't a database source of the World's")
    if source is None and len(held) != 1:
        raise ValueError(
            "the World has no database source to type cases into"
            if not held
            else f"name the source to type into: {', '.join(held)}"
        )
    return source or held[0]


# The person's expectation `thread`, whose head was `head` when they saw it, carried onto
# `case`, another case of its case's family, with the same data: a clinician's word that
# it still holds there.
def carry(view: View, thread: int, head: int, case: str) -> Written:
    edit, _, word = view.seen(thread)
    if word != "expectation":
        raise ValueError(f"{word} {thread} isn't an expectation")
    held = resolve(view.get, edit.digest, Expectation)
    family = view.catalog.family(held.case)
    if family is None or view.catalog.family(case) != family:
        raise ValueError(f"{case} isn't a case of the family {held.case} is of")
    carried = Expectation(
        case=case, expectation_schema=held.expectation_schema, data=held.data
    )
    return edit_component(view, thread, head, carried)
