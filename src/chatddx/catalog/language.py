from collections.abc import Callable, Collection, Iterable, Mapping

from chatddx.factors.base import Component, Resolver, iter_refs, language_tag, resolve
from chatddx.factors.cases import Case
from chatddx.factors.request import Compilation, Recipe, Skeleton, texts
from chatddx.factors.scoring import Expectation, Judge
from chatddx.factors.trial import Trial

from .families import family_of
from .model import LANGUAGE_KINDS, Edit, Subject
from .read import Reader, abouts


def language_of(rows: Reader, digest: str) -> str | None:
    return languages_of(rows, [digest])[digest]


def languages_of(rows: Reader, digests: Collection[str]) -> dict[str, str | None]:
    read = dict(rows.components(set(digests)))
    follows = {d: _follows(c) for d, c in read.items()}
    read |= dict(rows.components(set(follows.values()) - read.keys()))
    compiled = {
        d: found
        for d, c in read.items()
        if isinstance(c, Skeleton) and (found := rows.compilations(d))
    }
    voted, owned = _voted(rows, compiled, read.keys())
    families = {
        d: family
        for d, c in read.items()
        if isinstance(c, Case) and (family := family_of(rows, d)) is not None
    }
    said = abouts(rows, [Subject(family=f) for f in set(families.values())])

    def of(digest: str) -> str | None:
        if digest in families:
            return said[Subject(family=families[digest])].language
        return voted[digest] if digest in compiled else owned.get(digest)

    return {d: of(follows[d]) if d in follows else None for d in digests}


def _follows(component: Component) -> str:
    match component:
        case Expectation(case=case):
            return case
        case Trial(skeleton=skeleton) | Judge(skeleton=skeleton):
            return skeleton
        case _:
            return component.digest


def edit_languages(rows: Reader, edits: Collection[Edit]) -> dict[int, str | None]:
    named = {e.id: e.compilation for e in edits if e.compilation is not None}
    read = dict(rows.components(set(named.values())))
    compiled = {
        id: [resolve(read.__getitem__, digest, Compilation)]
        for id, digest in named.items()
    }
    voted, _ = _voted(rows, compiled, ())
    rest = languages_of(rows, {e.digest for e in edits if e.id not in voted})
    return {e.id: voted[e.id] if e.id in voted else rest[e.digest] for e in edits}


# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats these checks.
def check_language(rows: Reader, digest: str, value: str) -> str:
    kind = rows.kind(digest)
    if kind is None:
        raise LookupError(f"{digest} is not in the store")
    if kind not in LANGUAGE_KINDS:
        raise ValueError(f"{kind} components have no language of their own")
    if kind == "skeleton" and rows.compilations(digest):
        raise ValueError(
            f"{digest}: a compiled skeleton's language comes from its recipe"
        )
    _ = language_tag(value)
    return kind


def recipe_language(rows: Reader, recipe: Recipe) -> str | None:
    voters = _voters(recipe, rows.get)
    owned = dict(rows.languages({v for v in voters if v is not None}))
    return _vote(voters, owned.get)


def _voters(recipe: Recipe, get: Resolver) -> list[str | None]:
    return [
        getattr(recipe, part)
        for part in texts(recipe, get)
        if part != "appendix_layout"
    ]


def _vote(voters: list[str | None], owned: Callable[[str], str | None]) -> str | None:
    languages = {None if v is None else owned(v) for v in voters}
    return languages.pop() if len(languages) == 1 else None


def _agreed(votes: Iterable[str | None]) -> str | None:
    known = {v for v in votes if v is not None}
    return known.pop() if len(known) == 1 else None


def _voted[K](
    rows: Reader, compiled: Mapping[K, list[Compilation]], wanted: Collection[str]
) -> tuple[dict[K, str | None], dict[str, str]]:
    refs = {
        r.digest
        for found in compiled.values()
        for c in found
        if c.into is None
        for r in iter_refs(c.recipe)
    }
    chunks = dict(rows.components(refs))

    def get(digest: str) -> Component:
        return chunks[digest] if digest in chunks else rows.get(digest)

    voters = {
        k: [c.into or _voters(c.recipe, get) for c in found]
        for k, found in compiled.items()
    }
    written = {
        v
        for found in voters.values()
        for each in found
        if isinstance(each, list)
        for v in each
        if v is not None
    }
    owned = dict(rows.languages(set(wanted) | written))
    votes = {
        k: _agreed(
            each if isinstance(each, str) else _vote(each, owned.get) for each in found
        )
        for k, found in voters.items()
    }
    return votes, owned
