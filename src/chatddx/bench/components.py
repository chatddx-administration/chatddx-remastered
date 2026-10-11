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
from .seen import Seen
from .variation import PARTS

_UNLABELLED = "only a scorer's views and resources have labels"


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


def new(
    seen: Seen,
    component: Component | Recipe,
    name: str,
    language: str | None = None,
    labels: Labels | None = None,
) -> Written:
    if not isinstance(component, Recipe):
        return _written(
            seen, component, None, name=name, language=language, labels=labels
        )
    if language is not None:
        raise ValueError(COMPILED_LANGUAGE)
    if labels is not None:
        raise ValueError(_UNLABELLED)
    for part in PARTS:
        digest = getattr(component, part)
        if digest is not None and seen.rows.kind(digest) not in KINDS[part]:
            raise ValueError(f"{digest} isn't a stored chunk of {part}")
    registry, compilation = seen.compiled(component)
    with seen.conn.transaction():
        _ = seen.store.add(registry, [compilation.digest])
        edit = seen.catalog.create(
            compilation.skeleton,
            seen.person.id,
            compilation=compilation.digest,
            name=name,
        )
    return Written(edit, "created", seen.linted(compilation.skeleton))


def fork_component(
    seen: Seen,
    thread: int,
    name: str,
    component: Component | None = None,
    language: str | None = None,
    labels: Labels | None = None,
) -> Written:
    edit, _, word = seen.worded(thread)
    held = seen.get(edit.digest) if component is None else component
    seen.check_kind(thread, word, held)
    if labels is None and isinstance(held, Scorer) and held.digest == edit.digest:
        labels = seen.catalog.labels(edit.id)
    return _written(
        seen,
        held,
        None,
        name=name,
        language=language,
        forked_from=edit.id,
        labels=labels,
    )


def edit_component(
    seen: Seen,
    thread: int,
    head: int,
    component: Component,
    language: str | None = None,
    labels: Labels | None = None,
) -> Written:
    _, about, word = seen.worded(thread)
    if not about.owned_by(seen.person.id):
        raise NotFound(f"no {word} {thread} of yours")
    seen.check_kind(thread, word, component)
    return _written(
        seen, component, thread, language=language, head=head, labels=labels
    )


def _written(
    seen: Seen,
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
        seen.check_scorer(component)
    if isinstance(component, Expectation):
        seen.check_expecting(component, thread)
    if isinstance(component, Appendix):
        component = bound(seen, component)
    registry = seen.store.load(s.digest for s in component.refs())
    _ = registry.add(component)
    old = None if thread is None else seen.catalog.head(thread).digest
    with seen.conn.transaction():
        _ = seen.store.add(registry, [component.digest])
        if language is not None:
            keep_language(seen, component.digest, language)
        edit, kept = seen.catalog.keep(
            component.digest,
            seen.person.id,
            thread,
            name=name,
            forked_from=forked_from,
            head=head,
            labels=labels,
        )
        replaced = (
            _replaced(seen, old, component)
            if isinstance(component, Appendix) and old and kept == "edited"
            else {}
        )
    return Written(edit, SAVED[kept], seen.linted(component.digest), replaced)


def bound(seen: Seen, appendix: Appendix) -> Appendix:
    vignette = appendix.vignette
    families = {b.family for b in seen.rows.bindings_sharing(vignette)}
    if not any(
        seen.current(f) == vignette
        and seen.catalog.about(Subject(family=f)).shows(seen.person.id)
        for f in families
    ):
        raise ValueError(
            "an appendix is bound to the current vignette of a case you see"
        )
    text = appendix.text.replace("\r\n", "\n").replace("\r", "\n")
    return Appendix(vignette=vignette, text=text)


def _replaced(seen: Seen, old: str, new: Appendix) -> dict[str, str]:
    replaced: dict[str, str] = {}
    for digest in seen.store.reaching(old, "case"):
        case = resolve(seen.get, digest, Case)
        if case.vignette != new.vignette:
            continue
        held = tuple(new.digest if a == old else a for a in case.appendices)
        made = Case(vignette=case.vignette, appendices=held)
        registry = seen.store.load(held)
        _ = seen.store.add(registry, [registry.add(made)])
        replaced[digest] = made.digest
    return replaced


def keep_language(seen: Seen, digest: str, language: str) -> None:
    held = seen.catalog.language_of(digest)
    if held is not None and held != language:
        raise ValueError(
            f"{seen.title(digest)} is in {held} already: a text's language is the "
            + "same wherever it is held"
        )
    if held is None:
        seen.catalog.language(digest, language, seen.person.id)
