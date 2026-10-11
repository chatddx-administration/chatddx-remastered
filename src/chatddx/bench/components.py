from collections.abc import Mapping

from pydantic import JsonValue

from chatddx.catalog import LANGUAGE_KINDS, Labels, Subject
from chatddx.factors.base import Component, resolve
from chatddx.factors.cases import Appendix, Case
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.request import Recipe
from chatddx.factors.scoring import Expectation, Scorer

from .errors import NotFound
from .model import COMPILED_LANGUAGE, KINDS, SAVED, WRITTEN, Written
from .variation import PARTS
from .view import View

_UNLABELLED = "only a scorer's views and resources have labels"


# A component of a kind a person writes, from its JSON as the store gives it, `v`
# included or not.
def component(doc: Mapping[str, JsonValue]) -> Component:
    kind = doc.get("kind")
    if not isinstance(kind, str) or kind not in WRITTEN:
        raise ValueError(
            f"{kind!r} isn't a kind a person writes: the kinds are "
            + ", ".join(sorted(WRITTEN))
        )
    cls = BY_KIND[kind]
    given = {k: v for k, v in doc.items() if k != "v"}
    if doc.get("v", cls.schema_version) != cls.schema_version:
        raise ValueError(f"{kind} is at v{cls.schema_version}, not v{doc['v']}")
    return cls.model_validate(given)


# `component` as a new thread of the person's own, named `name`; a recipe is compiled by
# the running code and kept as a new configuration, with its compilation. A scorer is
# kept with `labels`.
def new(
    view: View,
    component: Component | Recipe,
    name: str,
    language: str | None = None,
    labels: Labels | None = None,
) -> Written:
    if not isinstance(component, Recipe):
        return _written(
            view, component, None, name=name, language=language, labels=labels
        )
    if language is not None:
        raise ValueError(COMPILED_LANGUAGE)
    if labels is not None:
        raise ValueError(_UNLABELLED)
    for part in PARTS:
        digest = getattr(component, part)
        if digest is not None and view.rows.kind(digest) not in KINDS[part]:
            raise ValueError(f"{digest} isn't a stored chunk of {part}")
    registry, compilation = view.compiled(component)
    with view.conn.transaction():
        _ = view.store.add(registry, [compilation.digest])
        edit = view.catalog.create(
            compilation.skeleton,
            view.person.id,
            compilation=compilation.digest,
            name=name,
        )
    return Written(edit, "created", view.linted(compilation.skeleton))


# A new thread of the person's own, named `name` and forked from the head of `thread`, a
# thread they see; it starts from `component` when given, else from the head. A scorer
# forked as it is keeps the head's labels unless given others.
def fork_component(
    view: View,
    thread: int,
    name: str,
    component: Component | None = None,
    language: str | None = None,
    labels: Labels | None = None,
) -> Written:
    edit, _, word = view.seen(thread)
    held = view.get(edit.digest) if component is None else component
    view.check_kind(thread, word, held)
    if labels is None and isinstance(held, Scorer) and held.digest == edit.digest:
        labels = view.catalog.labels(edit.id)
    return _written(
        view,
        held,
        None,
        name=name,
        language=language,
        forked_from=edit.id,
        labels=labels,
    )


# `component` as a new version of `thread`, a thread the person owns whose head was
# `head` when they saw it; nothing is written when it is the head already. A scorer is
# kept with `labels`: without them, the head's when it is the head's scorer, else none.
def edit_component(
    view: View,
    thread: int,
    head: int,
    component: Component,
    language: str | None = None,
    labels: Labels | None = None,
) -> Written:
    _, about, word = view.seen(thread)
    if not about.owned_by(view.person.id):
        raise NotFound(f"no {word} {thread} of yours")
    view.check_kind(thread, word, component)
    return _written(
        view, component, thread, language=language, head=head, labels=labels
    )


def _written(
    view: View,
    component: Component,
    thread: int | None,
    *,
    name: str | None = None,
    language: str | None = None,
    forked_from: int | None = None,
    head: int | None = None,
    labels: Labels | None = None,
) -> Written:
    kind = component.kind_name
    if kind not in WRITTEN:
        raise ValueError(f"a person doesn't write {kind} components")
    if language is not None and kind not in LANGUAGE_KINDS:
        raise ValueError(f"{kind} components have no language of their own")
    if labels is not None and not isinstance(component, Scorer):
        raise ValueError(_UNLABELLED)
    if isinstance(component, Scorer):
        view.check_scorer(component)
    if isinstance(component, Expectation):
        view.check_expecting(component, thread)
    if isinstance(component, Appendix):
        component = bound(view, component)
    registry = view.store.load(s.digest for s in component.refs())
    _ = registry.add(component)
    old = None if thread is None else view.catalog.head(thread).digest
    with view.conn.transaction():
        _ = view.store.add(registry, [component.digest])
        if language is not None:
            keep_language(view, component.digest, language)
        edit, kept = view.catalog.keep(
            component.digest,
            view.person.id,
            thread,
            name=name,
            forked_from=forked_from,
            head=head,
            labels=labels,
        )
        replaced = (
            _replaced(view, old, component)
            if isinstance(component, Appendix) and old and kept == "edited"
            else {}
        )
    return Written(edit, SAVED[kept], view.linted(component.digest), replaced)


# An appendix as the bench keeps it: its line endings LF, as browsers send CRLF, and bound
# to the current vignette of a family the person sees.
def bound(view: View, appendix: Appendix) -> Appendix:
    vignette = appendix.vignette
    families = {b.family for b in view.rows.bindings_sharing(vignette)}
    if not any(
        view.current(f) == vignette
        and view.catalog.about(Subject(family=f)).shows(view.person.id)
        for f in families
    ):
        raise ValueError(
            "an appendix is bound to the current vignette of a case you see"
        )
    text = appendix.text.replace("\r\n", "\n").replace("\r", "\n")
    return Appendix(vignette=vignette, text=text)


# Each stored case that holds the appendix `old` at `new`'s vignette, stored again with
# `new` in its place; no expectation moves with it.
def _replaced(view: View, old: str, new: Appendix) -> dict[str, str]:
    replaced: dict[str, str] = {}
    for digest in view.store.reaching(old, "case"):
        case = resolve(view.get, digest, Case)
        if case.vignette != new.vignette:
            continue
        held = tuple(new.digest if a == old else a for a in case.appendices)
        made = Case(vignette=case.vignette, appendices=held)
        registry = view.store.load(held)
        _ = view.store.add(registry, [registry.add(made)])
        replaced[digest] = made.digest
    return replaced


# A component's language is its text's, so other threads may hold it too: one it has is
# kept, and the person's is written only where it has none.
def keep_language(view: View, digest: str, language: str) -> None:
    held = view.catalog.language_of(digest)
    if held is not None and held != language:
        raise ValueError(
            f"{view.title(digest)} is in {held} already: a text's language is the "
            + "same wherever it is held"
        )
    if held is None:
        view.catalog.language(digest, language, view.person.id)
