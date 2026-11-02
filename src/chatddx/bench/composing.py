from collections.abc import Mapping

from chatddx.catalog import LANGUAGE_KINDS, About, Subject, read, threads, titles
from chatddx.catalog.language import recipe_language
from chatddx.factors.base import Component, Resolver
from chatddx.factors.request import (
    CHUNK_PARTS,
    Recipe,
    Translations,
    remapped,
    texts,
    translated,
)
from chatddx.identity import owns, sees

from .components import edit, fork, new
from .configurations import kept
from .errors import NotFound
from .model import Written
from .seen import Seen
from .variation import TriedVariation

type Drafts = Mapping[str, Component | None]


def drafted(
    seen: Seen,
    thread: int,
    head: int | None,
    before: Drafts,
    after: Drafts,
    into: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, tuple[str, ...]], dict[str, dict[str, str]]]:
    """The texts a configuration's recipe would hold with the chunks drafted in
    place of its own, by part, and the translations given for the texts `before`
    held carried over to them. Reads the recipe's chunks; writes nothing."""
    recipe = _recipe(seen, thread, head)
    held = _texts(seen, recipe, after)
    return held, remapped(_texts(seen, recipe, before), held, into)


def compose(
    seen: Seen,
    thread: int,
    head: int,
    chunks: Drafts,
    model: str | None = None,
    into: Mapping[str, Mapping[str, str]] | None = None,
    name: str | None = None,
) -> Written:
    """Saves the configuration with the chunks given in place of its own at `head`:
    a version of it, or a fork of it named `name`. Each chunk that changed is written
    to the thread its own came from, as a new version where that is the person's, or
    else as a fork of it under its name; a fork of the configuration forks those it
    changes. Its translations are `into` when given, or else its own carried over to
    the texts that changed. One transaction, locking each thread it writes."""
    variation = seen.variation(thread, None, head)
    recipe = variation.recipe
    if recipe is None:
        raise ValueError(f"{variation.name} has no recipe to save its parts in")
    if stray := sorted(set(chunks) - set(CHUNK_PARTS) - {"translations"}):
        raise ValueError(
            f"no part {stray[0]!r}: the parts are {', '.join(CHUNK_PARTS)}"
        )
    language = recipe_language(seen.rows, recipe)
    given = dict(chunks)
    if into is None:
        own = translated(recipe, seen.store.get)
        before = _texts(seen, recipe, {})
        moved = remapped(before, _texts(seen, recipe, given), own)
        into = moved if moved != own else None
    if into is not None:
        given["translations"] = (
            Translations(into={k: dict(v) for k, v in into.items()}) if into else None
        )
    with seen.conn.transaction():
        for part, chunk in given.items():
            old = getattr(recipe, part)
            if (None if chunk is None else chunk.digest) == old:
                continue
            if chunk is not None:
                written = _related(seen, variation, part, old, chunk, language, name)
                digest = written.edit.digest
            else:
                digest = None
            variation = variation.set(
                part, digest, "none" if digest is None else seen.title(digest)
            )
        if model is not None and model != recipe.model:
            variation = variation.set("model", model, seen.title(model))
        return kept(
            seen, variation, None if name else thread, name, None if name else head
        )


def _related(
    seen: Seen,
    variation: TriedVariation,
    part: str,
    old: str | None,
    chunk: Component,
    language: str | None,
    forking: str | None,
) -> Written:
    spoken = language if chunk.kind_name in LANGUAGE_KINDS else None
    held = [] if old is None else _holders(seen, old)
    mine = [t for t, a in held if owns(seen.person.id, a)]
    if mine and forking is None:
        at = threads.head(seen.rows, mine[0]).id
        return edit(seen, mine[0], at, chunk, spoken)
    if held:
        origin, about = next(((t, a) for t, a in held if t in mine), held[0])
        named = about.name or titles.title(seen.rows, origin)
        return fork(seen, origin, named, chunk, spoken)
    return new(seen, chunk, f"{variation.name} {part.replace('_', ' ')}", spoken)


def _holders(seen: Seen, digest: str) -> list[tuple[int, About]]:
    heads = read.heads_holding(seen.rows, [digest])
    known = read.abouts(seen.rows, [Subject(thread=t) for t in heads])
    return [
        (t, a)
        for t in heads
        if not (a := known[Subject(thread=t)]).deleted and sees(seen.person.id, a)
    ]


def _recipe(seen: Seen, thread: int, head: int | None) -> Recipe:
    recipe = seen.variation(thread, None, head).recipe
    if recipe is None:
        raise NotFound(f"no recipe of configuration {thread}")
    return recipe


def _texts(seen: Seen, recipe: Recipe, drafts: Drafts) -> dict[str, tuple[str, ...]]:
    held = {d.digest: d for d in drafts.values() if d is not None}
    changes = {
        p: None if d is None else d.digest
        for p, d in drafts.items()
        if p in CHUNK_PARTS
    }
    drafted = recipe.model_copy(update=changes)

    def get(digest: str) -> Component:
        return held[digest] if digest in held else seen.store.get(digest)

    resolver: Resolver = get
    return texts(drafted, resolver)
