from collections.abc import Callable, Collection, Iterable

from chatddx.factors.base import Component, Resolver, iter_refs, resolve
from chatddx.factors.request import Recipe, texts
from chatddx.factors.scoring import Expectation, Judge
from chatddx.factors.trial import Trial

from .families import family_of
from .model import LANGUAGE_KINDS, Entry, EntryField, Subject, language_tag, latest
from .read import Reader, about


def own(rows: Reader, digest: str) -> str | None:
    return latest(rows.languages([digest])).get(digest)


def language_of(rows: Reader, digest: str) -> str | None:
    match rows.kind(digest):
        case "case":
            family = family_of(rows, digest)
            if family is None:
                return None
            return about(rows, Subject(family=family)).language
        case "expectation":
            return language_of(rows, resolve(rows.get, digest, Expectation).case)
        case "trial":
            return language_of(rows, resolve(rows.get, digest, Trial).skeleton)
        case "judge":
            return language_of(rows, resolve(rows.get, digest, Judge).skeleton)
        case "skeleton":
            compilations = rows.compilations(digest)
            if not compilations:
                return own(rows, digest)
            return _agreed(recipe_language(rows, c.recipe) for c in compilations)
        case _:
            return own(rows, digest)


def languages_of(rows: Reader, digests: Collection[str]) -> dict[str, str | None]:
    wanted = set(digests)
    kinds = {d: c.kind_name for d, c in rows.components(wanted)}
    compiled = {d: rows.compilations(d) for d, k in kinds.items() if k == "skeleton"}
    refs = {
        r.digest
        for found in compiled.values()
        for c in found
        for r in iter_refs(c.recipe)
    }
    chunks = dict(rows.components(refs))

    def get(digest: str) -> Component:
        return chunks[digest] if digest in chunks else rows.get(digest)

    voters = {
        d: [_voters(c.recipe, get) for c in found] for d, found in compiled.items()
    }
    written = {
        v for found in voters.values() for each in found for v in each if v is not None
    }
    owned = latest(rows.languages(wanted | written))
    found: dict[str, str | None] = {}
    for digest in wanted:
        match kinds.get(digest):
            case "case" | "expectation" | "trial" | "judge":
                found[digest] = language_of(rows, digest)
            case "skeleton" if voters[digest]:
                votes = (_vote(each, owned.get) for each in voters[digest])
                found[digest] = _agreed(votes)
            case _:
                found[digest] = owned.get(digest)
    return found


# src/chatddx/store/migrations/0012-t2-catalog.sql repeats these checks.
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


# src/chatddx/store/migrations/0012-t2-catalog.sql repeats this check.
def check_entry(subject: Subject, entry: Entry) -> None:
    if entry.field == EntryField.LANGUAGE and subject.family is None:
        raise ValueError(
            "a language entry is for a family's vignette; "
            + "a component's language is kept on its digest"
        )


def recipe_language(rows: Reader, recipe: Recipe) -> str | None:
    return _vote(_voters(recipe, rows.get), lambda digest: own(rows, digest))


def _voters(recipe: Recipe, get: Resolver) -> list[str | None]:
    if recipe.translations is not None:
        return [recipe.translations]
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
